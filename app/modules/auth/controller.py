from app.modules.auth.service import AuthService


class AuthController:
    def __init__(self):
        self.service = AuthService()

    def request_otp(self, phone: str):
        return self.service.request_otp(phone)

    def verify_otp(self, phone: str, otp: str):
        return self.service.verify_otp(phone, otp)