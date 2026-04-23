from app.db.connection import get_connection
import string
from datetime import datetime


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
            "from_location": row[1],
            "to_location": row[2],
            "departure_time": row[3].isoformat() if row[3] else None,
            "price": float(row[4]),
            "created_at": row[5].isoformat() if row[5] else None
        }

    # ---------------- CREATE SHOW ----------------
    def create_show(self, data):

        conn = get_connection()
        cur = conn.cursor()

        try:
            cur.execute("""
                INSERT INTO shows (from_location, to_location, departure_time, price)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (
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
                SELECT id, from_location, to_location, departure_time, price, created_at
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

            if hasattr(data, 'from_location') and data.from_location:
                updates.append("from_location = %s")
                params.append(data.from_location.strip())

            if hasattr(data, 'to_location') and data.to_location:
                updates.append("to_location = %s")
                params.append(data.to_location.strip())

            if hasattr(data, 'departure_time') and data.departure_time:
                updates.append("departure_time = %s")
                params.append(data.departure_time)

            if hasattr(data, 'price') and data.price:
                updates.append("price = %s")
                params.append(data.price)

            if not updates:
                return {
                    "status": "error",
                    "message": "No fields to update",
                    "data": None
                }

            params.append(show_id)
            query = f"UPDATE shows SET {', '.join(updates)} WHERE id = %s RETURNING id"

            cur.execute(query, params)
            row = cur.fetchone()

            if not row:
                return {
                    "status": "error",
                    "message": "Show not found",
                    "data": None
                }

            conn.commit()

            return self.get_show(show_id)

        except Exception as e:
            conn.rollback()
            return {
                "status": "error",
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
                SELECT id, from_location, to_location, departure_time, price, created_at
                FROM shows WHERE id=%s
            """, (show_id,))

            row = cur.fetchone()

            if not row:
                return {"status": "error", "data": None}

            return {
                "status": "success",
                "data": self._format_show(row)
            }

        finally:
            cur.close()
            conn.close()

    # ---------------- LIST SHOWS ----------------
    def list_shows(self, from_location, to_location):

        conn = get_connection()
        cur = conn.cursor()

        try:
            query = """
                SELECT id, from_location, to_location, departure_time, price, created_at
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
                "data": [{"id": r[0], "seat_label": r[1]} for r in rows]
            }

        finally:
            cur.close()
            conn.close()

    # ---------------- PENDING SEATS (with expiry cleanup) ----------------
    def get_pending_seats(self, show_id):

        conn = get_connection()
        cur = conn.cursor()

        try:
            # First expire old pending bookings
            cur.execute("""
                UPDATE bookings
                SET status = 'EXPIRED'
                WHERE status = 'PENDING'
                  AND expires_at < NOW()
                  AND show_id = %s
            """, (show_id,))
            conn.commit()
            
            # Now get active pending seats (not expired)
            cur.execute("""
                SELECT bs.seat_id
                FROM booking_seats bs
                JOIN bookings b ON b.id = bs.booking_id
                WHERE b.show_id = %s
                  AND b.status = 'PENDING'
                  AND b.expires_at > NOW()
            """, (show_id,))

            rows = cur.fetchall()

            return {
                "status": "success",
                "data": [r[0] for r in rows]
            }

        except Exception as e:
            return {
                "status": "error",
                "data": []
            }
        finally:
            cur.close()
            conn.close()