from app.db.connection import get_connection


class AuthRepository:

    # ---------------- USER ----------------
    def get_user_by_phone(self, phone: str):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, phone_number, is_verified FROM users WHERE phone_number=%s",
            (phone,)
        )

        user = cur.fetchone()

        cur.close()
        conn.close()
        return user

    def create_user(self, phone: str):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO users (phone_number, is_verified)
            VALUES (%s, TRUE)
            RETURNING id, phone_number, is_verified
            """,
            (phone,)
        )

        user = cur.fetchone()

        conn.commit()
        cur.close()
        conn.close()
        return user

    def mark_verified(self, phone: str):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "UPDATE users SET is_verified=TRUE WHERE phone_number=%s",
            (phone,)
        )

        conn.commit()
        cur.close()
        conn.close()

    # ---------------- OTP ----------------
    def save_otp(self, phone: str, otp: str):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            INSERT INTO otp_verifications (phone_number, otp_code, expires_at, verified)
            VALUES (%s, %s, NOW() + INTERVAL '2 minutes', FALSE)
            ON CONFLICT (phone_number)
            DO UPDATE SET
                otp_code = EXCLUDED.otp_code,
                expires_at = EXCLUDED.expires_at,
                verified = FALSE
            """,
            (phone, otp)
        )

        conn.commit()
        cur.close()
        conn.close()

    def get_otp(self, phone: str):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT otp_code, expires_at, verified
            FROM otp_verifications
            WHERE phone_number=%s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (phone,)
        )

        otp = cur.fetchone()

        cur.close()
        conn.close()
        return otp