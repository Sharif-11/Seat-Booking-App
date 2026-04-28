from fastapi import APIRouter, Depends
from app.modules.booking.controller import BookingController
from app.modules.auth.middleware import get_current_user
from app.modules.booking.schemas import BookingRequestSchema, PaymentResultSchema

router = APIRouter()

controller = BookingController()
#  Get My Bookings

@router.get("/")
def get_my_bookings(user=Depends(get_current_user)):
    return  controller.get_my_bookings(user["user_id"])

# download ticket for a booking
@router.get("/{booking_id}/ticket")
def download_ticket(booking_id: int, user=Depends(get_current_user)):
    return controller.download_ticket(booking_id, user["user_id"])

# -------------------------
# 🎟 CREATE BOOKING
# -------------------------
@router.post("/")
async def create_booking(
    payload: BookingRequestSchema,
    user=Depends(get_current_user)
):
    return await controller.create_booking(payload, user)


# -------------------------
# ✅ PAYMENT SUCCESS → CONFIRM BOOKING
# -------------------------
@router.post("/{booking_id}/success")
async def confirm_booking(
    booking_id: int,
    payload: PaymentResultSchema,
    user=Depends(get_current_user)
):
    return await controller.confirm_booking(booking_id, payload, user)


# -------------------------
# ❌ PAYMENT FAILED → CANCEL BOOKING
# -------------------------
@router.post("/{booking_id}/failed")
async def failed_booking(
    booking_id: int,
    payload: PaymentResultSchema,
    user=Depends(get_current_user)
):
    return await controller.failed_booking(booking_id, payload, user)