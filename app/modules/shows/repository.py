from app.db.connection import get_connection
import string
from datetime import datetime, timezone


# ---------------- SEAT GENERATION ----------------
def generate_seats(show_id: int, seat_count: int):
    seats = []
    row_letters = string.ascii_uppercase

    rows = []
    full_rows = seat_count // 4
    remainder = seat_count % 4

    for _ in range(full_rows):
        rows.append(4)

    if remainder > 0:
        if rows:
            rows[-1] += remainder
        else:
            rows.append(remainder)

    for i in range(len(rows) - 1, -1, -1):
        while rows[i] > 5:
            overflow = rows[i] - 5
            rows[i] = 5
            if i == 0:
                rows.insert(0, overflow)
            else:
                rows[i - 1] += overflow

    for i, seat_in_row in enumerate(rows):
        row = row_letters[i]
        for j in range(1, seat_in_row + 1):
            seats.append((show_id, f"{row}{j}"))

    return seats


class ShowRepository:

    # ---------------- FORMAT ----------------
    def _format_show(self, row):
        if not row:
            return None

        return {
            "id": row[0],
            "title": row[5],  # 🔥 moved up for clarity
            "from_location": row[1],
            "to_location": row[2],
            "departure_time": row[3].isoformat() if row[3] else None,
            "price": float(row[4]),
            "created_at": row[6].isoformat() if row[6] else None
        }

    # ---------------- CREATE SHOW ----------------
    def create_show(self, data):
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO shows (title, from_location, to_location, departure_time, price)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                data["title"],
                data["from_location"],
                data["to_location"],
                data["departure_time"],
                data["price"]
            ))

            show_id = cur.fetchone()[0]

            seats = generate_seats(show_id, data["seat_count"])

            cur.executemany("""
                INSERT INTO seats (show_id, seat_label)
                VALUES (%s, %s)
            """, seats)

            cur.execute("""
                SELECT id, from_location, to_location, departure_time, price, title, created_at
                FROM shows WHERE id=%s
            """, (show_id,))

            show = self._format_show(cur.fetchone())

            conn.commit()

            return {
                "status": "success",
                "status_code": 201,
                "message": "Show created successfully",
                "data": show
            }

        except Exception as e:
            conn.rollback()
            return {
                "status": "error",
                "status_code": 500,
                "message": str(e),
                "data": None
            }

        finally:
            cur.close()
            conn.close()

    # ---------------- UPDATE SHOW ----------------
    def update_show(self, show_id, data):
        conn = get_connection()
        cur = conn.cursor()

        try:
            updates = []
            params = []

            if hasattr(data, 'title') and data.title:
                updates.append("title = %s")
                params.append(data.title.strip())

            if hasattr(data, 'from_location') and data.from_location:
                updates.append("from_location = %s")
                params.append(data.from_location.strip())

            if hasattr(data, 'to_location') and data.to_location:
                updates.append("to_location = %s")
                params.append(data.to_location.strip())

            if hasattr(data, 'departure_time') and data.departure_time:
                updates.append("departure_time = %s")
                params.append(data.departure_time)

            if hasattr(data, 'price') and data.price is not None:
                updates.append("price = %s")
                params.append(data.price)

            if not updates:
                return {
                    "status": "error",
                    "status_code": 400,
                    "message": "No fields to update",
                    "data": None
                }

            params.append(show_id)

            query = f"""
                UPDATE shows
                SET {', '.join(updates)}
                WHERE id = %s
                RETURNING id, from_location, to_location, departure_time, price, title, created_at
            """

            cur.execute(query, params)
            row = cur.fetchone()

            if not row:
                return {
                    "status": "error",
                    "status_code": 404,
                    "message": "Show not found",
                    "data": None
                }

            conn.commit()

            return {
                "status": "success",
                "status_code": 200,
                "message": "Show updated successfully",
                "data": self._format_show(row)
            }

        except Exception as e:
            conn.rollback()
            return {
                "status": "error",
                "status_code": 500,
                "message": str(e),
                "data": None
            }

        finally:
            cur.close()
            conn.close()

    # ---------------- GET SHOW ----------------
    def get_show(self, show_id):
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT id, from_location, to_location, departure_time, price, title, created_at
                FROM shows WHERE id=%s
            """, (show_id,))

            row = cur.fetchone()

            if not row:
                return {
                    "status": "error",
                    "status_code": 404,
                    "message": "Show not found",
                    "data": None
                }

            return {
                "status": "success",
                "status_code": 200,
                "data": self._format_show(row)
            }

        finally:
            cur.close()
            conn.close()

    # ---------------- LIST SHOWS ----------------
    def list_shows(self, from_location=None, to_location=None):
        conn = get_connection()
        cur = conn.cursor()

        try:
            query = """
                SELECT id, from_location, to_location, departure_time, price, title, created_at
                FROM shows WHERE 1=1
            """
            params = []

            if from_location:
                query += " AND from_location ILIKE %s"
                params.append(f"%{from_location}%")

            if to_location:
                query += " AND to_location ILIKE %s"
                params.append(f"%{to_location}%")

            query += " ORDER BY departure_time"

            cur.execute(query, tuple(params))
            rows = cur.fetchall()

            return {
                "status": "success",
                "status_code": 200,
                "data": [self._format_show(r) for r in rows]
            }

        finally:
            cur.close()
            conn.close()

    # ---------------- SEATS ----------------
    def get_seats_by_show(self, show_id):
        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                SELECT id, seat_label
                FROM seats
                WHERE show_id=%s
                ORDER BY seat_label
            """, (show_id,))

            rows = cur.fetchall()

            return {
                "status": "success",
                "status_code": 200,
                "data": [{"id": r[0], "seat_label": r[1]} for r in rows]
            }

        finally:
            cur.close()
            conn.close()

    # ---------------- PENDING SEATS (FIXED TIMESTAMP) ----------------
    def get_pending_seats(self, show_id):
        conn = get_connection()
        cur = conn.cursor()

        try:
            # FIXED: Use NOW() AT TIME ZONE 'UTC' for consistent UTC timezone
            cur.execute("""
                UPDATE bookings
                SET status = 'EXPIRED'
                WHERE status = 'PENDING'
                  AND expires_at < (NOW() AT TIME ZONE 'UTC')
                  AND show_id = %s
            """, (show_id,))
            conn.commit()

            # FIXED: Also use NOW() AT TIME ZONE 'UTC' in the SELECT query
            cur.execute("""
                SELECT bs.seat_id
                FROM booking_seats bs
                JOIN bookings b ON b.id = bs.booking_id
                WHERE b.show_id = %s
                  AND b.status = 'PENDING'
                  AND b.expires_at > (NOW() AT TIME ZONE 'UTC')
            """, (show_id,))

            rows = cur.fetchall()

            return {
                "status": "success",
                "status_code": 200,
                "data": [r[0] for r in rows]
            }

        except Exception as e:
            return {
                "status": "error",
                "status_code": 500,
                "message": str(e),
                "data": []
            }

        finally:
            cur.close()
            conn.close()

    # ---------------- ADDITIONAL HELPER: GET AVAILABLE SEATS ----------------
    def get_available_seats(self, show_id):
        """Get all seats that are not confirmed or pending for a show"""
        conn = get_connection()
        cur = conn.cursor()

        try:
            # First expire old pending bookings
            cur.execute("""
                UPDATE bookings
                SET status = 'EXPIRED'
                WHERE status = 'PENDING'
                  AND expires_at < (NOW() AT TIME ZONE 'UTC')
                  AND show_id = %s
            """, (show_id,))
            conn.commit()

            # Get all seats for the show
            cur.execute("""
                SELECT s.id, s.seat_label
                FROM seats s
                WHERE s.show_id = %s
                ORDER BY s.seat_label
            """, (show_id,))
            
            all_seats = cur.fetchall()
            
            # Get booked/confirmed seats
            cur.execute("""
                SELECT DISTINCT bs.seat_id
                FROM booking_seats bs
                JOIN bookings b ON b.id = bs.booking_id
                WHERE b.show_id = %s
                  AND b.status IN ('CONFIRMED', 'PENDING')
                  AND (b.status = 'CONFIRMED' OR b.expires_at > (NOW() AT TIME ZONE 'UTC'))
            """, (show_id,))
            
            booked_seat_ids = {row[0] for row in cur.fetchall()}
            
            # Filter available seats
            available_seats = []
            for seat_id, seat_label in all_seats:
                if seat_id not in booked_seat_ids:
                    available_seats.append({
                        "id": seat_id,
                        "seat_label": seat_label,
                        "is_available": True
                    })
                else:
                    available_seats.append({
                        "id": seat_id,
                        "seat_label": seat_label,
                        "is_available": False
                    })
            
            return {
                "status": "success",
                "status_code": 200,
                "data": available_seats
            }
            
        except Exception as e:
            return {
                "status": "error",
                "status_code": 500,
                "message": str(e),
                "data": []
            }
        finally:
            cur.close()
            conn.close()