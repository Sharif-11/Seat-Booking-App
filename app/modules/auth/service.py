import random
import jwt
import datetime
from datetime import timezone, timedelta

from app.config.settings import settings
from app.modules.auth.repository import AuthRepository


class AuthService:

    def __init__(self):
        self.repo = AuthRepository()

    # ---------------- OTP ----------------
    def _generate_otp(self):
        return str(random.randint(100000, 999999))

    # ---------------- JWT (FIXED TIMEZONE) ----------------
    def _generate_token(self, user_id, phone):
        payload = {
            "user_id": user_id,
            "phone": phone,
            "exp": datetime.datetime.now(timezone.utc) + datetime.timedelta(days=7)
        }

        return jwt.encode(
            payload,
            settings.JWT_SECRET,
            algorithm="HS256"
        )

    # ---------------- HELPER: Check OTP expiry ----------------
    def _is_otp_expired(self, expires_at):
        """Check if OTP has expired with proper timezone handling"""
        current_time = datetime.datetime.now(timezone.utc)
        
        if expires_at is None:
            return True
        
        # Handle string conversion if needed
        if isinstance(expires_at, str):
            expires_at = datetime.datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        # Ensure expires_at is timezone-aware
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        # Add a small buffer (2 seconds) to avoid race conditions
        buffer_seconds = 2
        return current_time > (expires_at + timedelta(seconds=buffer_seconds))

    # ---------------- HELPER: Get remaining OTP validity ----------------
    def _get_otp_remaining_seconds(self, expires_at):
        """Get remaining seconds before OTP expires"""
        if expires_at is None:
            return 0
            
        current_time = datetime.datetime.now(timezone.utc)
        
        if isinstance(expires_at, str):
            expires_at = datetime.datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        remaining = (expires_at - current_time).total_seconds()
        return max(0, int(remaining))

    # ---------------- REQUEST OTP ----------------
    def request_otp(self, phone: str):
        user = self.repo.get_user_by_phone(phone)

        # Already verified user
        if user and user[2] is True:  # is_verified
            token = self._generate_token(user[0], phone)
            return {
                "status": "success",
                "status_code": 200,
                "message": "User already verified",
                "data": {
                    "user_id": user[0],
                    "phone": phone,
                    "token": token
                }
            }

        otp_data = self.repo.get_otp(phone)

        # Cooldown check (2 min window)
        if otp_data and otp_data[0] is not None:  # Check if OTP exists
            otp_code, expires_at, verified = otp_data

            if not verified:
                # Check if the existing OTP is still valid (not expired)
                if not self._is_otp_expired(expires_at):
                    remaining_seconds = self._get_otp_remaining_seconds(expires_at)
                    return {
                        "status": "success",
                        "status_code": 200,
                        "message": f"OTP already sent. Please wait. OTP valid for {remaining_seconds} more seconds.",
                        "data": {
                            "remaining_seconds": remaining_seconds
                        }
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
        
        # Check if user exists and already verified
        if user and user[2] is True:  # is_verified
            token = self._generate_token(user[0], phone)
            return {
                "status": "success",
                "status_code": 200,
                "message": "User already verified",
                "data": {
                    "user_id": user[0],
                    "phone": phone,
                    "token": token
                }
            }
        
        otp_data = self.repo.get_latest_unverified_otp(phone)

        if not otp_data:
            # Check if there's any OTP at all
            any_otp = self.repo.get_otp(phone)
            if any_otp and any_otp[0] is not None:
                stored_otp, expires_at, verified = any_otp
                if verified:
                    return {
                        "status": "error",
                        "status_code": 400,
                        "message": "OTP already used. Please request a new OTP."
                    }
                if self._is_otp_expired(expires_at):
                    return {
                        "status": "error",
                        "status_code": 410,
                        "message": "OTP expired. Please request a new OTP."
                    }
            
            return {
                "status": "error",
                "status_code": 400,
                "message": "OTP not found. Please request a new OTP."
            }

        stored_otp, expires_at, verified, user_id = otp_data

        # Check if already verified
        if verified:
            return {
                "status": "error",
                "status_code": 400,
                "message": "OTP already used. Please request a new OTP."
            }

        # Debug logging
        current_time = datetime.datetime.now(timezone.utc)
        print(f"[DEBUG] Current time: {current_time.isoformat()}")
        print(f"[DEBUG] Expires at: {expires_at.isoformat() if hasattr(expires_at, 'isoformat') else expires_at}")
        print(f"[DEBUG] Time remaining: {self._get_otp_remaining_seconds(expires_at)} seconds")

        # Expiry check
        if self._is_otp_expired(expires_at):
            remaining = self._get_otp_remaining_seconds(expires_at)
            return {
                "status": "error",
                "status_code": 410,
                "message": f"OTP expired. Please request a new OTP. (Valid for {remaining} more seconds)"
            }

        if stored_otp != otp:
            return {
                "status": "error",
                "status_code": 400,
                "message": "Invalid OTP"
            }

        # Mark OTP as verified
        self.repo.mark_otp_verified(user_id)

        # Create user if not exists (though it should exist from OTP request)
        if not user:
            user = self.repo.create_user(phone)
        else:
            # Mark existing user as verified
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

    # ---------------- RESEND OTP ----------------
    def resend_otp(self, phone: str):
        """Force resend OTP regardless of cooldown"""
        otp = self._generate_otp()
        self.repo.save_otp(phone, otp)
        
        print(f"[OTP DEBUG] Resent OTP for {phone} -> {otp}")
        
        return {
            "status": "success",
            "status_code": 200,
            "message": "OTP resent successfully"
        }

    # ---------------- REFRESH TOKEN ----------------
    def refresh_token(self, user_id: int, phone: str):
        """Generate a new token for existing user"""
        token = self._generate_token(user_id, phone)
        
        return {
            "status": "success",
            "status_code": 200,
            "message": "Token refreshed successfully",
            "data": {
                "user_id": user_id,
                "phone": phone,
                "token": token
            }
        }

    # ---------------- CHECK OTP STATUS ----------------
    def check_otp_status(self, phone: str):
        """Check if there's a valid OTP for the phone number"""
        otp_data = self.repo.get_latest_unverified_otp(phone)
        
        if not otp_data:
            return {
                "status": "error",
                "status_code": 404,
                "message": "No active OTP found"
            }
        
        stored_otp, expires_at, verified, user_id = otp_data
        
        if verified:
            return {
                "status": "error",
                "status_code": 400,
                "message": "OTP already used"
            }
        
        if self._is_otp_expired(expires_at):
            return {
                "status": "error",
                "status_code": 410,
                "message": "OTP expired"
            }
        
        remaining_seconds = self._get_otp_remaining_seconds(expires_at)
        
        return {
            "status": "success",
            "status_code": 200,
            "message": "OTP is valid",
            "data": {
                "remaining_seconds": remaining_seconds,
                "expires_at": expires_at.isoformat() if hasattr(expires_at, 'isoformat') else expires_at
            }
        }