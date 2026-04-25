from fastapi import HTTPException

from app.modules.payment.repository import PaymentRepository
from app.modules.booking.repository import BookingRepository
from app.config.redis import get_redis
from app.config.Cache_key import CacheKey


class PaymentService:

    def __init__(self):
        self.repo = PaymentRepository()
        self.booking_repo = BookingRepository()
       

    # -------------------------
    # 🔐 Validate Booking
    # -------------------------
    async def _validate_booking(self, booking_id: int, user_id: int):
        booking = await self.booking_repo.get_by_id(booking_id)

        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")

        # booking[1] = user_id (based on table order)
        if booking[1] != user_id:
            raise HTTPException(status_code=403, detail="Unauthorized")

        return booking

    # -------------------------
    # ✅ SUCCESS PAYMENT
    # -------------------------
    async def payment_success(self, booking_id: int, user_id: int, provider: str):

        booking =await self._validate_booking(booking_id, user_id)

        # booking[3] = status
        if booking[3] != "PENDING":
            raise HTTPException(status_code=400, detail="Invalid booking state")

        existing = self.repo.get_by_booking_id(booking_id)
        if existing:
            return {
                "status": "success",
                "status_code": 200,
                "message": "Payment already processed",
                "data": existing
            }

        # booking[4] = total_amount
        payment = self.repo.create_payment(
            booking_id,
            provider,
            booking[4],
            "SUCCESS"
        )

        await self.booking_repo.update_status(booking_id, "CONFIRMED")

        # invalidate redis cached booked for a show id 
        show_id = booking[2]  # show_id
        redis = get_redis()
        if redis:
            booked_key = CacheKey.booked_seats(show_id)
            await redis.delete(booked_key)


       

        return {
            "status": "success",
            "status_code": 200,
            "message": "Payment successful",
            "data": payment
        }

    # -------------------------
    # ❌ FAIL PAYMENT
    # -------------------------
    def payment_fail(self, booking_id: int, user_id: int, provider: str):

        booking = self._validate_booking(booking_id, user_id)

        # 🔥 Release Redis seat locks
        seats = self.booking_repo.get_booking_seats(booking_id)

        show_id = booking[2]  # show_id

        for seat in seats:
            seat_id = seat[0]
            key = f"seat_lock:{show_id}:{seat_id}"
            self.redis.delete(key)

        # booking[4] = total_amount
        payment = self.repo.create_payment(
            booking_id,
            provider,
            booking[4],
            "FAILED"
        )

        # ❗ delete booking (cascade seats)
        self.booking_repo.delete_booking(booking_id)

        return {
            "status": "error",
            "status_code": 400,
            "message": "Payment failed, booking cancelled",
            "data": payment
        }

    # -------------------------
    # 🔍 GET PAYMENT
    # -------------------------
    async def get_payment(self, booking_id: int, user_id: int):

        await self._validate_booking(booking_id, user_id)

        booking = self.booking_repo.get_booking(booking_id)

        return {
            "status": "success",
            "status_code": 200,
            "message": "Payment fetched",
            "data": booking
        }