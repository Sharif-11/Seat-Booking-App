import uuid
from datetime import datetime, timedelta, timezone
from app.db.connection import get_connection
from app.config.settings import settings
from app.config.Cache_key import CacheKey
from app.config.redis import get_redis


class BookingRepository:

    # -------------------------
    # Helper to get current UTC time from database
    # -------------------------
    def _get_current_utc(self, cur=None):
        """Get current UTC time from database to ensure consistency"""
        if cur:
            # Use existing cursor
            cur.execute("SELECT NOW() AT TIME ZONE 'UTC'")
            return cur.fetchone()[0]
        else:
            # Create new connection if no cursor provided
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute("SELECT NOW() AT TIME ZONE 'UTC'")
                current_utc = cur.fetchone()[0]
                return current_utc
            finally:
                cur.close()
                conn.close()

    # -------------------------
    # 🧹 Unified Expiry Method - Handles DELETION of expired bookings
    # -------------------------
    def _expire_old_bookings_for_show(self, conn, cur, show_id=None):
        """
        DELETE old PENDING bookings and their associated seats.
        If show_id is provided, only delete for specific show.
        If show_id is None, delete for all shows.
        
        NOTE: This method DELETES records. Use only when you need to free up seats.
        """
        try:
            # Get current UTC time from database
            current_utc = self._get_current_utc(cur)
            
            # Build the WHERE clause based on whether show_id is provided
            show_filter = ""
            params = [current_utc]
            if show_id:
                show_filter = " AND show_id = %s"
                params.append(show_id)
            
            print(f"[INFO] Deleting expired bookings at {current_utc.isoformat()} for show_id: {show_id if show_id else 'ALL'}")
            
            # Step 1: Delete booking_seats for expired bookings
            cur.execute(f"""
                DELETE FROM booking_seats
                WHERE booking_id IN (
                    SELECT id 
                    FROM bookings 
                    WHERE status = 'PENDING'
                      AND expires_at < %s
                      {show_filter}
                )
            """, params)
            
            deleted_seats_count = cur.rowcount
            
            # Step 2: Delete the expired bookings
            cur.execute(f"""
                DELETE FROM bookings
                WHERE status = 'PENDING'
                  AND expires_at < %s
                  {show_filter}
                RETURNING id, show_id
            """, params)
            
            deleted_bookings = cur.fetchall()
            deleted_bookings_count = len(deleted_bookings)
            
            # Commit the changes
            conn.commit()
            
            if deleted_bookings_count > 0 or deleted_seats_count > 0:
                print(f"[INFO] Deleted {deleted_bookings_count} expired bookings and {deleted_seats_count} seat reservations for show_id: {show_id if show_id else 'ALL'}")
                
            return {
                "deleted_bookings_count": deleted_bookings_count,
                "deleted_seats_count": deleted_seats_count,
                "deleted_bookings": deleted_bookings
            }
            
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Failed to delete expired bookings for show_id {show_id if show_id else 'ALL'}: {e}")
            raise e
    async def invalidate_cache_for_booking(self, booking_id,seat_ids):
        for seat_id in seat_ids:
            cache_key = CacheKey.seat_lock(booking_id, seat_id)
            # Invalidate the cache for this seat
            await get_redis().delete(cache_key)
    # -------------------------
    # 🔍 Check already CONFIRMED seats
    # -------------------------
    def check_seats_taken(self, show_id, seat_ids):
        conn = get_connection()
        cur = conn.cursor()

        try:
            # Delete expired bookings to free up seats before checking
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
                "message": f"Failed to check seats: {str(e)}"
            }
        finally:
            cur.close()
            conn.close()

    # -------------------------
    # 🚀 Create Booking
    # -------------------------
    def create_booking(self, user_id, show_id, seat_ids, amount):
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            # Delete expired bookings for this show first to free up seats
            self._expire_old_bookings_for_show(conn, cur, show_id)

            # Get current UTC time from database
            current_utc = self._get_current_utc(cur)
            expires_at = current_utc + timedelta(seconds=settings.SEAT_LOCK_TTL)

            cur.execute("""
                INSERT INTO bookings (
                    user_id,
                    show_id,
                    status,
                    total_amount,
                    expires_at,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                user_id,
                show_id,
                "PENDING",
                amount,
                expires_at,
                current_utc
            ))

            booking_id = cur.fetchone()[0]

            cur.executemany("""
                INSERT INTO booking_seats (booking_id, seat_id)
                VALUES (%s, %s)
            """, [(booking_id, s) for s in seat_ids])

            conn.commit()

            expires_at_iso = expires_at.isoformat() if expires_at else None

            return {
                "status": "success",
                "status_code": 201,
                "data": {
                    "booking_id": booking_id,
                    "seat_ids": seat_ids,
                    "show_id": show_id,
                    "total_amount": float(amount),
                    "expires_at": expires_at_iso
                }
            }

        except Exception as e:
            conn.rollback()
            return {
                "status": "error",
                "status_code": 500,
                "message": str(e)
            }

        finally:
            cur.close()
            conn.close()

    # -------------------------
    # 📖 Get booking - NO DELETION, just check and return status
    # -------------------------
    def get_booking(self, booking_id):
        conn = get_connection()
        cur = conn.cursor()

        try:
            # Get booking details
            cur.execute("""
                SELECT id, user_id, show_id, status, total_amount, expires_at
                FROM bookings
                WHERE id = %s
            """, (booking_id,))

            row = cur.fetchone()

            if not row:
                return {"status": "error", "message": "Booking not found"}

            booking_id, user_id, show_id, status, total_amount, expires_at = row
            
            # Check if the booking is expired but not yet deleted
            if status == 'PENDING' and expires_at:
                # Get current time from database
                current_utc = self._get_current_utc(cur)
                
                if expires_at < current_utc:
                    # Return as EXPIRED without deleting
                    return {
                        "status": "success",
                        "data": {
                            "booking_id": booking_id,
                            "user_id": user_id,
                            "show_id": show_id,
                            "status": "EXPIRED",
                            "total_amount": float(total_amount),
                            "expires_at": expires_at.isoformat() if hasattr(expires_at, 'isoformat') else str(expires_at),
                            "seat_ids": []
                        }
                    }
            
            # Get seats only for non-expired bookings
            seat_ids = []
            if status != 'EXPIRED':
                cur.execute("""
                    SELECT seat_id FROM booking_seats WHERE booking_id = %s
                """, (booking_id,))
                seat_ids = [r[0] for r in cur.fetchall()]

            expires_at_iso = None
            if expires_at:
                expires_at_iso = expires_at.isoformat() if hasattr(expires_at, 'isoformat') else str(expires_at)

            return {
                "status": "success",
                "data": {
                    "booking_id": booking_id,
                    "user_id": user_id,
                    "show_id": show_id,
                    "status": status,
                    "total_amount": float(total_amount),
                    "expires_at": expires_at_iso,
                    "seat_ids": seat_ids
                }
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}
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
            # Get booking info first
            cur.execute("""
                SELECT status, show_id, expires_at FROM bookings WHERE id = %s
            """, (booking_id,))
            
            row = cur.fetchone()
            
            if not row:
                return {"status": "error", "message": "Booking not found"}
            
            booking_status, show_id, expires_at = row
            
            if booking_status == 'CONFIRMED':
                return {"status": "error", "message": "Cannot cancel confirmed booking"}
            
            if booking_status == 'EXPIRED':
                # invalide cache if any and return error
                
                return {"status": "error", "message": "Booking already expired"}
            
            # Check if PENDING but expired
            if booking_status == 'PENDING' and expires_at:
                current_utc = self._get_current_utc(cur)
                if expires_at < current_utc:
                    return {"status": "error", "message": "Booking already expired"}
            
         
            
            # Cancel the booking if it's still PENDING
            cur.execute("""
                UPDATE bookings
                SET status = 'CANCELLED'
                WHERE id = %s AND status = 'PENDING'
                RETURNING id
            """, (booking_id,))

            row = cur.fetchone()
            conn.commit()

            if not row:
                return {"status": "error", "message": "Booking cannot be cancelled"}

            return {
                "status": "success",
                "message": "Booking cancelled successfully",
                "data": {"booking_id": row[0]}
            }

        except Exception as e:
            conn.rollback()
            return {"status": "error", "message": str(e)}

        finally:
            cur.close()
            conn.close()
    def failed_booking(self, booking_id,user_id):
        conn=get_connection()
        cur=conn.cursor()
        try:
            # fetch booking info first
            cur.execute("""
                SELECT status, show_id, expires_at FROM bookings WHERE id = %s AND user_id = %s
            """, (booking_id, user_id))
            row = cur.fetchone()
            if not row:
                return {"status": "error", "message": "Booking not found"}
            booking_status, show_id, expires_at = row
            if booking_status == 'CONFIRMED':
                return {"status": "error", "message": "Cannot mark confirmed booking as failed"}
            # now we need to fetch seats for this booking to invalidate cache
            cur.execute("""
                SELECT seat_id FROM booking_seats WHERE booking_id = %s
            """, (booking_id,))
            seat_ids = [r[0] for r in cur.fetchall()]
            # now delete the booking and associated seats
            cur.execute("""
                DELETE FROM booking_seats WHERE booking_id = %s
            """, (booking_id,))
            cur.execute("""
                DELETE FROM bookings WHERE id = %s
            """, (booking_id,))
            conn.commit()
            return {
                "status": "success",
                "message": "Booking marked as failed and deleted",
                "data": {
                    "booking_id": booking_id,
                    "show_id": show_id,
                    "seat_ids": seat_ids
                }
            }
        except Exception as e:
            conn.rollback()
            return {"status": "error", "message": str(e)}
        
    # -------------------------
    # 💳 CONFIRM BOOKING + PAYMENT
    # -------------------------
    def confirm_booking_with_payment(
        self,
        booking_id,
        amount,
        wallet_name,
        wallet_phone,
        idempotency_key=None
    ):
        conn = get_connection()
        cur = conn.cursor()

        try:
            # -------------------------
            # 1️⃣ Idempotency check
            # -------------------------
            if idempotency_key:
                cur.execute("""
                    SELECT id, transaction_id
                    FROM payments
                    WHERE idempotency_key = %s
                """, (idempotency_key,))

                existing = cur.fetchone()

                if existing:
                    return {
                        "status": "success",
                        "message": "Already processed",
                        "data": {
                            "payment_id": existing[0],
                            "transaction_id": existing[1]
                        }
                    }

            # -------------------------
            # 2️⃣ Get booking info
            # -------------------------
            cur.execute("""
                SELECT status, expires_at, total_amount, show_id
                FROM bookings
                WHERE id = %s
            """, (booking_id,))

            row = cur.fetchone()

            if not row:
                return {"status": "error", "message": "Booking not found"}

            status, expires_at, total_amount, show_id = row

            if status != "PENDING":
                return {"status": "error", "message": f"Invalid status {status}"}

            # Check if expired
            if expires_at:
                current_utc = self._get_current_utc(cur)
                if expires_at < current_utc:
                    # Delete expired bookings for this show to clean up
                    self._expire_old_bookings_for_show(conn, cur, show_id)
                    return {"status": "error", "message": "Booking expired"}
            
            # -------------------------
            # 3️⃣ Confirm booking
            # -------------------------
            cur.execute("""
                UPDATE bookings
                SET status = 'CONFIRMED', expires_at = NULL
                WHERE id = %s AND status = 'PENDING'
                RETURNING id
            """, (booking_id,))

            if not cur.fetchone():
                conn.rollback()
                return {"status": "error", "message": "Booking could not be confirmed"}

            # -------------------------
            # 4️⃣ Create payment
            # -------------------------
            transaction_id = str(uuid.uuid4())
            current_utc = self._get_current_utc(cur)

            cur.execute("""
                INSERT INTO payments (
                    booking_id,
                    transaction_id,
                    amount,
                    status,
                    idempotency_key,
                    wallet_name,
                    wallet_phone,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                booking_id,
                transaction_id,
                amount or total_amount,
                "SUCCESS",
                idempotency_key,
                wallet_name,
                wallet_phone,
                current_utc
            ))

            payment_id = cur.fetchone()[0]

            conn.commit()

            return {
                "status": "success",
                "message": "Booking confirmed + payment created",
                "data": {
                    "booking_id": booking_id,
                    "payment_id": payment_id,
                    "transaction_id": transaction_id
                }
            }

        except Exception as e:
            conn.rollback()
            return {"status": "error", "message": str(e)}

        finally:
            cur.close()
            conn.close()

    # -------------------------
    # 🧹 Manual cleanup method for old bookings (can be called by a scheduler)
    # -------------------------
    def cleanup_all_expired_bookings(self):
        """Manually delete expired bookings across all shows"""
        conn = get_connection()
        cur = conn.cursor()
        
        try:
            result = self._expire_old_bookings_for_show(conn, cur, show_id=None)
            return {
                "status": "success",
                "message": "Cleanup completed",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Cleanup failed: {str(e)}"
            }
        finally:
            cur.close()
            conn.close()