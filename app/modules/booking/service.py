import json
from app.config.redis import get_redis
from app.modules.booking.repository import BookingRepository
from app.modules.shows.repository import ShowRepository


SEAT_LOCK_TTL = 120  # 2 minutes lock for pending bookings


class BookingService:

    def __init__(self):
        self.repo = BookingRepository()
        self.show_repo = ShowRepository()

    def _seat_lock_key(self, show_id, seat_id):
        return f"seat_lock:{show_id}:{seat_id}"

    def _booking_lock_key(self, show_id):
        return f"booking_lock:{show_id}"

    def _booked_cache_key(self, show_id):
        return f"seat_booked:{show_id}"

    # -------------------------
    # 🚀 CREATE BOOKING
    # -------------------------
    async def create_booking(self, payload, user):

        redis = get_redis()

        show_id = payload.show_id
        seat_ids = list(set(payload.seat_ids))
        user_id = user["user_id"]

        booking_lock_key = self._booking_lock_key(show_id)

        # 1️⃣ Global lock to prevent race conditions
        if redis:
            lock = await redis.set(booking_lock_key, "1", nx=True, ex=5)
            if not lock:
                return {
                    "status": "error",
                    "status_code": 429,
                    "message": "Too many booking requests"
                }

        try:
            # 2️⃣ Check if show exists
            show_res = self.show_repo.get_show(show_id)
            show = show_res.get("data")

            if not show:
                return {
                    "status": "error",
                    "status_code": 404,
                    "message": "Show not found"
                }

            # 3️⃣ Check seat availability (Redis fast check)
            if redis:
                booked_key = self._booked_cache_key(show_id)

                raw = await redis.get(booked_key)
                booked = set(json.loads(raw)) if raw else set()

                for seat_id in seat_ids:
                    if str(seat_id) in booked:
                        return {
                            "status": "error",
                            "status_code": 409,
                            "message": f"Seat {seat_id} already booked"
                        }

                    lock_key = self._seat_lock_key(show_id, seat_id)
                    if await redis.get(lock_key):
                        return {
                            "status": "error",
                            "status_code": 409,
                            "message": f"Seat {seat_id} is currently reserved"
                        }

            else:
                # DB fallback (check CONFIRMED bookings only)
                unavailable = self.repo.check_seats_taken(show_id, seat_ids)

                if unavailable and unavailable.get("data"):
                    return {
                        "status": "error",
                        "status_code": 409,
                        "message": "Seats already booked",
                        "data": unavailable.get("data")
                    }

            # 4️⃣ Calculate total amount
            total_amount = float(show["price"]) * len(seat_ids)

            # 5️⃣ Lock seats in Redis (for pending booking duration)
            if redis:
                locked_seats = []
                try:
                    for seat_id in seat_ids:
                        key = self._seat_lock_key(show_id, seat_id)
                        locked = await redis.set(key, user_id, nx=True, ex=SEAT_LOCK_TTL)

                        if not locked:
                            return {
                                "status": "error",
                                "status_code": 409,
                                "message": f"Seat {seat_id} just got reserved"
                            }
                        locked_seats.append(seat_id)
                except Exception as e:
                    # Rollback any locks we already set
                    for seat_id in locked_seats:
                        await redis.delete(self._seat_lock_key(show_id, seat_id))
                    raise e

            # 6️⃣ Create booking in database (PENDING state)
            booking = self.repo.create_booking(
                user_id=user_id,
                show_id=show_id,
                seat_ids=seat_ids,
                amount=total_amount
            )

            if not booking.get("data"):
                # Rollback Redis locks if DB fails
                if redis:
                    for seat_id in seat_ids:
                        await redis.delete(self._seat_lock_key(show_id, seat_id))
                
                return {
                    "status": "error",
                    "status_code": 500,
                    "message": "Failed to create booking"
                }

            booking_id = booking["data"]["booking_id"]

            # 7️⃣ Store idempotency key if provided
            if redis and hasattr(payload, "idempotency_key") and payload.idempotency_key:
                id_key = f"booking_idempotency:{user_id}:{show_id}:{payload.idempotency_key}"
                await redis.set(id_key, booking_id, ex=600)

            return booking

        finally:
            if redis:
                await redis.delete(booking_lock_key)
    
    # -------------------------
    # ✅ CONFIRM BOOKING (Move from PENDING to CONFIRMED)
    # -------------------------
    async def confirm_booking(self, booking_id, user_id):
        redis = get_redis()
        
        # Get booking details first
        booking = self.repo.get_booking(booking_id)
        
        if not booking or booking.get("data", {}).get("user_id") != user_id:
            return {
                "status": "error",
                "status_code": 404,
                "message": "Booking not found"
            }
        
        booking_data = booking["data"]
        
        if booking_data["status"] != "PENDING":
            return {
                "status": "error",
                "status_code": 400,
                "message": f"Cannot confirm booking with status: {booking_data['status']}"
            }
        
        # Check if expired
        if booking_data.get("expires_at"):
            from datetime import datetime
            expires_at = datetime.fromisoformat(booking_data["expires_at"])
            if expires_at < datetime.utcnow():
                return {
                    "status": "error",
                    "status_code": 410,
                    "message": "Booking has expired"
                }
        
        # Confirm in DB
        result = self.repo.confirm_booking(booking_id)
        
        if result.get("status") == "success" and redis:
            # Add seats to booked_cache
            show_id = booking_data["show_id"]
            seat_ids = booking_data["seat_ids"]
            booked_key = self._booked_cache_key(show_id)
            
            try:
                raw = await redis.get(booked_key)
                booked = set(json.loads(raw)) if raw else set()
                booked.update(map(str, seat_ids))
                await redis.set(booked_key, json.dumps(list(booked)), ex=3600)
                
                # Remove seat locks (no longer needed as they're confirmed)
                for seat_id in seat_ids:
                    lock_key = self._seat_lock_key(show_id, seat_id)
                    await redis.delete(lock_key)
                    
            except Exception:
                pass
        
        return result
    
    # -------------------------
    # ❌ CANCEL BOOKING
    # -------------------------
    async def cancel_booking(self, booking_id, user_id):
        redis = get_redis()
        
        # Get booking details first
        booking = self.repo.get_booking(booking_id)
        
        if not booking or booking.get("data", {}).get("user_id") != user_id:
            return {
                "status": "error",
                "status_code": 404,
                "message": "Booking not found"
            }
        
        booking_data = booking["data"]
        show_id = booking_data["show_id"]
        seat_ids = booking_data["seat_ids"]
        
        # Cancel in DB
        result = self.repo.cancel_booking(booking_id)
        
        if result.get("status") == "success" and redis:
            # If it was CONFIRMED, remove from booked_cache
            if booking_data["status"] == "CONFIRMED":
                booked_key = self._booked_cache_key(show_id)
                try:
                    raw = await redis.get(booked_key)
                    if raw:
                        booked = set(json.loads(raw))
                        booked.difference_update(map(str, seat_ids))
                        await redis.set(booked_key, json.dumps(list(booked)), ex=3600)
                except Exception:
                    pass
            
            # Always remove seat locks if they exist (for PENDING bookings)
            for seat_id in seat_ids:
                lock_key = self._seat_lock_key(show_id, seat_id)
                await redis.delete(lock_key)
        
        return result
    
    # -------------------------
    # 🔍 GET BOOKING DETAILS
    # -------------------------
    async def get_booking(self, booking_id, user_id):
        booking = self.repo.get_booking(booking_id)
        
        if not booking or booking.get("data", {}).get("user_id") != user_id:
            return {
                "status": "error",
                "status_code": 404,
                "message": "Booking not found"
            }
        
        return booking
    
    # -------------------------
    # 👤 GET USER BOOKINGS
    # -------------------------
    async def get_user_bookings(self, user_id):
        return self.repo.get_user_bookings(user_id)