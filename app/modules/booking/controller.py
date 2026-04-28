from app.modules.booking.service import BookingService


class BookingController:

    def __init__(self):
        self.service = BookingService()
    
    # Get My Bookings
    def get_my_bookings(self, user_id):
        return  self.service.get_bookings_by_user_id(user_id)
    # download ticket for a booking
    def download_ticket(self, booking_id, user_id):
        return self.service.download_ticket(booking_id, user_id)

    # -------------------------
    # 🎟 CREATE BOOKING
    # -------------------------
    async def create_booking(self, payload, user):
        return await self.service.create_booking(payload, user)

    # -------------------------
    # ✅ CONFIRM BOOKING (PAYMENT SUCCESS)
    # -------------------------
    async def confirm_booking(self, booking_id, payload, user):
        return await self.service.confirm_booking(
            booking_id=booking_id,
            user_id=user["user_id"],
            wallet_name=payload.wallet_name,
            wallet_phone=payload.wallet_phone,
            idempotency_key=payload.idempotency_key
        )

    # -------------------------
    # ❌ PAYMENT FAILED → CANCEL
    # -------------------------
    async def failed_booking(self, booking_id, payload, user):
        return await self.service.failed_booking(
            booking_id=booking_id,
          user_id=user["user_id"]
        )