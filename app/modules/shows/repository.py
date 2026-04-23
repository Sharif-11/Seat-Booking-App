from app.db.connection import get_connection
import string


# ---------------- SEAT GENERATION ----------------
def generate_seats(show_id: int, seat_count: int):
    seats = []
    row_letters = string.ascii_uppercase

    rows = []
    full_rows = seat_count // 4
    remainder = seat_count % 4

    # base rows
    for _ in range(full_rows):
        rows.append(4)

    # merge remainder if < 4
    if remainder > 0:
        if remainder < 4:
            if rows:
                rows[-1] += remainder
            else:
                rows.append(remainder)
        else:
            rows.append(remainder)

    # rebalance (max 5 per row)
    for i in range(len(rows) - 1, -1, -1):
        while rows[i] > 5:
            overflow = rows[i] - 5
            rows[i] = 5
            if i == 0:
                rows.insert(0, overflow)
            else:
                rows[i - 1] += overflow

    # generate seat labels
    for i, seat_in_row in enumerate(rows):
        row_letter = row_letters[i]
        for j in range(1, seat_in_row + 1):
            seats.append((show_id, f"{row_letter}{j}"))

    return seats


class ShowRepository:

    # ---------------- HELPER ----------------
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
    async def create_show(self, data):
        conn = get_connection()
        cur = conn.cursor()

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

        # generate seats
        seats = generate_seats(show_id, data["seat_count"])

        cur.executemany("""
            INSERT INTO seats (show_id, seat_label)
            VALUES (%s, %s)
        """, seats)

        # fetch created show
        cur.execute("""
            SELECT id, from_location, to_location, departure_time, price, created_at
            FROM shows
            WHERE id=%s
        """, (show_id,))

        show = self._format_show(cur.fetchone())

        conn.commit()
        cur.close()
        conn.close()

        return {
            "status": "success",
            "status_code": 201,
            "message": "Show created successfully",
            "data": show
        }

    # ---------------- UPDATE SHOW ----------------
    async def update_show(self, show_id, data):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            UPDATE shows
            SET from_location=%s,
                to_location=%s,
                departure_time=%s,
                price=%s
            WHERE id=%s
            RETURNING id, from_location, to_location, departure_time, price, created_at
        """, (
            data.from_location.strip(),
            data.to_location.strip(),
            data.departure_time,
            data.price,
            show_id
        ))

        updated = cur.fetchone()

        conn.commit()
        cur.close()
        conn.close()

        if not updated:
            return {
                "status": "error",
                "status_code": 404,
                "message": "Show not found",
                "data": None
            }

        return {
            "status": "success",
            "status_code": 200,
            "message": "Show updated successfully",
            "data": self._format_show(updated)
        }

    # ---------------- LIST SHOWS ----------------
    async def list_shows(self, from_location, to_location):
        conn = get_connection()
        cur = conn.cursor()

        query = """
            SELECT id, from_location, to_location, departure_time, price, created_at
            FROM shows
            WHERE 1=1
        """
        params = []

        if from_location:
            query += " AND from_location ILIKE %s"
            params.append(f"%{from_location}%")

        if to_location:
            query += " AND to_location ILIKE %s"
            params.append(f"%{to_location}%")

        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        shows = [self._format_show(row) for row in rows]

        cur.close()
        conn.close()

        return {
            "status": "success",
            "status_code": 200,
            "message": "Shows fetched successfully",
            "data": shows
        }

    # ---------------- GET SINGLE SHOW ----------------
    async def get_show(self, show_id):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, from_location, to_location, departure_time, price, created_at
            FROM shows
            WHERE id=%s
        """, (show_id,))

        row = cur.fetchone()

        cur.close()
        conn.close()

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
            "message": "Show fetched successfully",
            "data": self._format_show(row)
        }

    # ---------------- GET SEATS ----------------
    async def get_seats_by_show(self, show_id):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, seat_label
            FROM seats
            WHERE show_id=%s
            ORDER BY seat_label
        """, (show_id,))

        rows = cur.fetchall()

        seats = [
            {
                "id": row[0],
                "seat_label": row[1]
            }
            for row in rows
        ]

        cur.close()
        conn.close()

        return {
            "status": "success",
            "status_code": 200,
            "message": "Seat map fetched successfully",
            "data": seats
        }