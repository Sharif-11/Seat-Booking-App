import random
import jwt
import datetime

from app.config.settings import settings
from app.modules.auth.repository import AuthRepository


class AuthService:

    def __init__(self):
        self.repo = AuthRepository()

    # ---------------- OTP ----------------
    def _generate_otp(self):
        return str(random.randint(100000, 999999))

    # ---------------- JWT ----------------
    def _generate_token(self, user_id, phone):
        payload = {
            "user_id": user_id,
            "phone": phone,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }

        return jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm="HS256"
        )

    # ---------------- REQUEST OTP ----------------
    def request_otp(self, phone: str):

        user = self.repo.get_user_by_phone(phone)

        # already verified user
        if user and user[2] is True:
            return {
                "status": "success",
                "status_code": 200,
                "message": "User already verified"
            }

        otp_data = self.repo.get_otp(phone)

        # cooldown check (2 min window)
        if otp_data:
            otp_code, expires_at, verified = otp_data

            if not verified:
                return {
                    "status": "success",
                    "status_code": 200,
                    "message": "OTP already sent. Please wait."
                }

        otp = self._generate_otp()
        self.repo.save_otp(phone, otp)

        print(f"[OTP DEBUG] {phone} -> {otp}")

        return {
            "status": "success",
            "status_code": 200,
            "message": "OTP sent successfully"
        }

    # ---------------- VERIFY OTP ----------------
    def verify_otp(self, phone: str, otp: str):

        user = self.repo.get_user_by_phone(phone)
        otp_data = self.repo.get_otp(phone)

        if not otp_data:
            return {
                "status": "error",
                "status_code": 400,
                "message": "OTP not found"
            }

        stored_otp, expires_at, verified = otp_data

        # expiry check
        if datetime.datetime.utcnow() > expires_at:
            return {
                "status": "error",
                "status_code": 410,
                "message": "OTP expired"
            }

        if stored_otp != otp:
            return {
                "status": "error",
                "status_code": 400,
                "message": "Invalid OTP"
            }

        # create user if not exists
        if not user:
            user = self.repo.create_user(phone)

        self.repo.mark_verified(phone)

        token = self._generate_token(user[0], phone)

        return {
            "status": "success",
            "status_code": 200,
            "message": "Verification successful",
            "data": {
                "user_id": user[0],
                "phone": phone,
                "token": token
            }
        }