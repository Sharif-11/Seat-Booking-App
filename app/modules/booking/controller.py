from app.modules.booking.service import BookingService


class BookingController:

    def __init__(self):
        self.service = BookingService()

    async def create_booking(self, payload, user):
        return await self.service.create_booking(payload, user)