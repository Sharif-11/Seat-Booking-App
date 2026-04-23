from datetime import datetime, timedelta
from app.db.connection import get_connection


class BookingRepository:

    # -------------------------
    # 🔍 Check already CONFIRMED seats (not PENDING)
    # -------------------------
    def check_seats_taken(self, show_id, seat_ids):

        conn = get_connection()
        cur = conn.cursor()

        try:
            # First, mark expired bookings as EXPIRED
            self._expire_old_bookings_for_show(conn, cur, show_id)
            
            query = """
                SELECT bs.seat_id
                FROM booking_seats bs
                JOIN bookings b ON b.id = bs.booking_id
                WHERE b.show_id = %s
                  AND b.status = 'CONFIRMED'
                  AND bs.seat_id = ANY(%s)
            """

            cur.execute(query, (show_id, seat_ids))
            rows = cur.fetchall()

            return {
                "status": "success",
                "status_code": 200,
                "message": "Seat check completed",
                "data": [row[0] for row in rows]
            }

        except Exception as e:
            return {
                "status": "error",
                "status_code": 500,
                "message": "Failed to check seats",
                "error": str(e),
                "data": []
            }

        finally:
            cur.close()
            conn.close()

    # -------------------------
    # 🧹 Expire old bookings for a specific show
    # -------------------------
    def _expire_old_bookings_for_show(self, conn, cur, show_id):
        """Mark expired PENDING bookings as EXPIRED for a specific show"""
        try:
            cur.execute("""
                UPDATE bookings
                SET status = 'EXPIRED'
                WHERE status = 'PENDING'
                  AND expires_at < NOW()
                  AND show_id = %s
                RETURNING id
            """, (show_id,))
            
            expired_ids = [row[0] for row in cur.fetchall()]
            
            if expired_ids:
                conn.commit()
                
            return expired_ids
            
        except Exception:
            conn.rollback()
            return []

    # -------------------------
    # 🧹 Expire all old bookings
    # -------------------------
    def _expire_old_bookings(self, conn, cur):
        """Mark expired PENDING bookings as EXPIRED"""
        try:
            cur.execute("""
                UPDATE bookings
                SET status = 'EXPIRED'
                WHERE status = 'PENDING'
                  AND expires_at < NOW()
                RETURNING id
            """)
            
            expired_ids = [row[0] for row in cur.fetchall()]
            
            if expired_ids:
                conn.commit()
                
            return expired_ids
            
        except Exception:
            conn.rollback()
            return []
    

    # we need a method to delete all expiredbooking for a show id
    def delete_expired_bookings_for_show(self, show_id):
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                DELETE FROM bookings
                WHERE status = 'EXPIRED'
                  AND show_id = %s
            """, (show_id,))
            
            deleted_count = cur.rowcount
            conn.commit()
            
            return {
                "status": "success",
                "status_code": 200,
                "message": f"Deleted {deleted_count} expired bookings for show {show_id}",
                "data": {"deleted_count": deleted_count}
            }
            
        except Exception as e:
            conn.rollback()
            return {
                "status": "error",
                "status_code": 500,
                "message": "Failed to delete expired bookings",
                "error": str(e),
                "data": None
            }

        finally:
            cur.close()
            conn.close()

    # -------------------------
    # 🚀 Create booking (PENDING)
    # -------------------------
    def create_booking(self, user_id, show_id, seat_ids, amount):

        conn = get_connection()
        cur = conn.cursor()

        try:
            expires_at = datetime.utcnow() + timedelta(minutes=10)

            # 1️⃣ Insert booking
            cur.execute("""
                INSERT INTO bookings (
                    user_id,
                    show_id,
                    status,
                    total_amount,
                    idempotency_key,
                    expires_at,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user_id,
                show_id,
                "PENDING",
                amount,
                None,
                expires_at,
                datetime.utcnow()
            ))

            booking_id = cur.fetchone()[0]

            # 2️⃣ Insert seats
            cur.executemany("""
                INSERT INTO booking_seats (booking_id, seat_id)
                VALUES (%s, %s)
            """, [(booking_id, s) for s in seat_ids])

            conn.commit()

            return {
                "status": "success",
                "status_code": 201,
                "message": "Booking created (PENDING)",
                "data": {
                    "booking_id": booking_id,
                    "status": "PENDING",
                    "total_amount": float(amount),
                    "seat_ids": seat_ids,
                    "show_id": show_id,
                    "expires_at": expires_at.isoformat()
                }
            }

        except Exception as e:
            conn.rollback()

            return {
                "status": "error",
                "status_code": 500,
                "message": "Booking creation failed",
                "error": str(e),
                "data": None
            }

        finally:
            cur.close()
            conn.close()
    
    # -------------------------
    # 📖 Get booking by ID (with expiry check)
    # -------------------------
    def get_booking(self, booking_id):
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            # Clean up expired bookings first
            self._expire_old_bookings(conn, cur)
            
            # Get booking details
            cur.execute("""
                SELECT id, user_id, show_id, status, total_amount, expires_at, created_at
                FROM bookings
                WHERE id = %s
            """, (booking_id,))
            
            booking_row = cur.fetchone()
            
            if not booking_row:
                return {
                    "status": "error",
                    "status_code": 404,
                    "message": "Booking not found",
                    "data": None
                }
            
            # Get seat IDs for this booking
            cur.execute("""
                SELECT seat_id
                FROM booking_seats
                WHERE booking_id = %s
            """, (booking_id,))
            
            seat_rows = cur.fetchall()
            seat_ids = [row[0] for row in seat_rows]
            
            return {
                "status": "success",
                "data": {
                    "booking_id": booking_row[0],
                    "user_id": booking_row[1],
                    "show_id": booking_row[2],
                    "status": booking_row[3],
                    "total_amount": float(booking_row[4]) if booking_row[4] else 0,
                    "expires_at": booking_row[5].isoformat() if booking_row[5] else None,
                    "created_at": booking_row[6].isoformat() if booking_row[6] else None,
                    "seat_ids": seat_ids
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "data": None
            }
        finally:
            cur.close()
            conn.close()

    # -------------------------
    # 👤 Get user bookings
    # -------------------------
    def get_user_bookings(self, user_id):
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            # Clean up expired bookings first
            self._expire_old_bookings(conn, cur)
            
            # Get all bookings for user
            cur.execute("""
                SELECT id, show_id, status, total_amount, expires_at, created_at
                FROM bookings
                WHERE user_id = %s
                ORDER BY created_at DESC
            """, (user_id,))
            
            bookings = []
            for row in cur.fetchall():
                # Get seat IDs for each booking
                cur.execute("""
                    SELECT seat_id
                    FROM booking_seats
                    WHERE booking_id = %s
                """, (row[0],))
                
                seat_ids = [r[0] for r in cur.fetchall()]
                
                bookings.append({
                    "booking_id": row[0],
                    "show_id": row[1],
                    "status": row[2],
                    "total_amount": float(row[3]) if row[3] else 0,
                    "expires_at": row[4].isoformat() if row[4] else None,
                    "created_at": row[5].isoformat() if row[5] else None,
                    "seat_ids": seat_ids
                })
            
            return {
                "status": "success",
                "data": bookings
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "data": []
            }
        finally:
            cur.close()
            conn.close()

    # -------------------------
    # ✅ Confirm booking (with expiry check)
    # -------------------------
    def confirm_booking(self, booking_id):
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            # Check if booking exists and is pending
            cur.execute("""
                SELECT status, expires_at
                FROM bookings
                WHERE id = %s
            """, (booking_id,))
            
            row = cur.fetchone()
            
            if not row:
                return {
                    "status": "error",
                    "status_code": 404,
                    "message": "Booking not found",
                    "data": None
                }
            
            status, expires_at = row
            
            if status != "PENDING":
                return {
                    "status": "error",
                    "status_code": 400,
                    "message": f"Cannot confirm booking with status: {status}",
                    "data": None
                }
            
            # Check if expired
            if expires_at and expires_at < datetime.utcnow():
                # Mark as expired first
                cur.execute("""
                    UPDATE bookings
                    SET status = 'EXPIRED'
                    WHERE id = %s
                """, (booking_id,))
                conn.commit()
                
                return {
                    "status": "error",
                    "status_code": 410,
                    "message": "Booking has expired",
                    "data": None
                }
            
            # Confirm the booking
            cur.execute("""
                UPDATE bookings
                SET status = 'CONFIRMED', expires_at = NULL
                WHERE id = %s AND status = 'PENDING'
                RETURNING id, status
            """, (booking_id,))
            
            row = cur.fetchone()
            conn.commit()
            
            return {
                "status": "success",
                "status_code": 200,
                "message": "Booking confirmed",
                "data": {
                    "booking_id": row[0],
                    "status": row[1]
                }
            }
            
        except Exception as e:
            conn.rollback()
            return {
                "status": "error",
                "status_code": 500,
                "message": "Confirmation failed",
                "error": str(e),
                "data": None
            }
        finally:
            cur.close()
            conn.close()

    # -------------------------
    # ❌ Cancel booking
    # -------------------------
    def cancel_booking(self, booking_id):

        conn = get_connection()
        cur = conn.cursor()

        try:
            # Don't allow cancelling expired bookings
            cur.execute("""
                UPDATE bookings
                SET status = 'CANCELLED'
                WHERE id = %s AND status IN ('PENDING', 'CONFIRMED')
                RETURNING id, status
            """, (booking_id,))

            row = cur.fetchone()

            if not row:
                return {
                    "status": "error",
                    "status_code": 404,
                    "message": "Booking not found or already expired",
                    "data": None
                }

            conn.commit()

            return {
                "status": "success",
                "status_code": 200,
                "message": "Booking cancelled",
                "data": {
                    "booking_id": row[0],
                    "status": row[1]
                }
            }

        except Exception as e:
            conn.rollback()

            return {
                "status": "error",
                "status_code": 500,
                "message": "Cancellation failed",
                "error": str(e),
                "data": None
            }

        finally:
            cur.close()
            conn.close()

    async def get_by_id(self, booking_id: int):
        conn = get_connection()
        cur = conn.cursor()

        try:
            query = "SELECT * FROM bookings WHERE id = %s"
            cur.execute(query, (booking_id,))
            return cur.fetchone()
        finally:
            cur.close()
            conn.close()
  
    async def update_status(self, booking_id: int, status: str):
        conn = get_connection()
        cur = conn.cursor()

        try:
            query = """
                UPDATE bookings
                SET status = %s
                WHERE id = %s
                RETURNING *
            """
            cur.execute(query, (status, booking_id))
            row = cur.fetchone()
            conn.commit()
            return row
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()