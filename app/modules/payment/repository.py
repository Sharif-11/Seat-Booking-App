from app.db.connection import get_connection


class PaymentRepository:

    def get_by_booking_id(self, booking_id: int):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM payments WHERE booking_id = %s",
            (booking_id,)
        )

        payment = cur.fetchone()

        cur.close()
        conn.close()
        return payment

    def create_payment(self, booking_id: int, provider: str, amount: float, status: str):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO payments (booking_id, provider, amount, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id, booking_id, provider, amount, status, created_at
            """,
            (booking_id, provider, amount, status)
        )

        payment = cur.fetchone()

        conn.commit()
        cur.close()
        conn.close()

        return payment