from fastapi import APIRouter, Depends

from app.modules.auth.middleware import get_current_user
from app.modules.payment.service import PaymentService

router = APIRouter()
service = PaymentService()


@router.post("/{booking_id}/success")
def payment_success(
    booking_id: int,
    provider: str,
    user=Depends(get_current_user)
):
    return service.payment_success(booking_id, user["id"], provider)


@router.post("/{booking_id}/fail")
def payment_fail(
    booking_id: int,
    provider: str,
    user=Depends(get_current_user)
):
    return service.payment_fail(booking_id, user["id"], provider)


@router.get("/{booking_id}")
def get_payment(
    booking_id: int,
    user=Depends(get_current_user)
):
    return service.get_payment(booking_id, user["id"])