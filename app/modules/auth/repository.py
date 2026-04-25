from app.db.connection import get_connection
from datetime import datetime, timezone


class AuthRepository:

    # ---------------- USER ----------------
    def get_user_by_phone(self, phone: str):
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id, phone_number, is_verified, otp_code, otp_expires_at, otp_verified FROM users WHERE phone_number=%s",
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

    # ---------------- OTP METHODS (now using users table) ----------------
    def save_otp(self, phone: str, otp: str):
        conn = get_connection()
        cur = conn.cursor()

        # Check if user exists
        cur.execute(
            "SELECT id FROM users WHERE phone_number=%s",
            (phone,)
        )
        user = cur.fetchone()

        if user:
            # Update existing user with OTP
            cur.execute(
                """
                UPDATE users 
                SET otp_code = %s,
                    otp_expires_at = (NOW() AT TIME ZONE 'UTC') + INTERVAL '2 minutes',
                    otp_verified = FALSE
                WHERE phone_number = %s
                """,
                (otp, phone)
            )
        else:
            # Create new user with OTP
            cur.execute(
                """
                INSERT INTO users (phone_number, is_verified, otp_code, otp_expires_at, otp_verified)
                VALUES (%s, FALSE, %s, (NOW() AT TIME ZONE 'UTC') + INTERVAL '2 minutes', FALSE)
                """,
                (phone, otp)
            )

        conn.commit()
        cur.close()
        conn.close()

    def get_otp(self, phone: str):
        """Get the latest OTP for a phone number"""
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT otp_code, otp_expires_at, otp_verified
            FROM users
            WHERE phone_number=%s
            """,
            (phone,)
        )

        otp = cur.fetchone()

        cur.close()
        conn.close()
        return otp

    def get_latest_unverified_otp(self, phone: str):
        """Get unverified OTP for a phone number"""
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            SELECT otp_code, otp_expires_at, otp_verified, id
            FROM users
            WHERE phone_number=%s AND otp_verified = FALSE
            """,
            (phone,)
        )

        otp = cur.fetchone()

        cur.close()
        conn.close()
        return otp

    def mark_otp_verified(self, otp_id: int):
        """Mark OTP as verified for a specific user"""
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE users
            SET otp_verified = TRUE,
                is_verified = TRUE
            WHERE id = %s
            """,
            (otp_id,)
        )

        conn.commit()
        cur.close()
        conn.close()

    def delete_expired_otps(self):
        """Clean up expired OTPs (optional maintenance method)"""
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            UPDATE users
            SET otp_code = NULL,
                otp_expires_at = NULL,
                otp_verified = FALSE
            WHERE otp_expires_at < (NOW() AT TIME ZONE 'UTC')
            """
        )

        updated_count = cur.rowcount
        conn.commit()
        cur.close()
        conn.close()
        
        return updated_count