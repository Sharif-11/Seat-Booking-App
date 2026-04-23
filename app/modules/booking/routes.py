from fastapi import APIRouter, Depends
from app.modules.booking.controller import BookingController
from app.modules.auth.middleware import get_current_user
from app.modules.booking.schemas import BookingRequestSchema

router = APIRouter()

controller = BookingController()


@router.post("/")
async def create_booking(payload: BookingRequestSchema, user=Depends(get_current_user)):
    return await controller.create_booking(payload, user)