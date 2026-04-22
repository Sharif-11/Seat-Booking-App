from fastapi import APIRouter, Response, Depends
from app.modules.auth.controller import AuthController
from app.modules.auth.schemas import RequestOTPInput, VerifyOTPInput

router = APIRouter()
controller = AuthController()


def sanitize_request(data):
    return data


@router.post("/request-otp")
def request_otp(payload: RequestOTPInput):
    payload = sanitize_request(payload)
    return controller.request_otp(payload.phone)


@router.post("/verify-otp")
def verify_otp(payload: VerifyOTPInput, response: Response):
    payload = sanitize_request(payload)

    result = controller.verify_otp(payload.phone, payload.otp)

    # set cookie if success
    if result["status"] == "success":
        response.set_cookie(
            key="token",
            value=result["data"]["token"],
            httponly=False,  # set True in production
            secure=False,  # set True in production (HTTPS)
            samesite="lax"
        )

    return result