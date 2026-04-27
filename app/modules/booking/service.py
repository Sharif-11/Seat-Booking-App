import json
from datetime import datetime, timezone
from app.config.redis import get_redis
from app.modules.booking.repository import BookingRepository
from app.modules.shows.repository import ShowRepository
from app.config.Cache_key import CacheKey
from app.config.settings import settings
from app.modules.redis.booking_gateway import BookingGateway


class BookingService:

    def __init__(self):
        self.repo = BookingRepository()
        self.show_repo = ShowRepository()

    # -------------------------
    # 🚀 CREATE BOOKING
    # -------------------------
    async def create_booking(self, payload, user):

        redis = get_redis()

        show_id = payload.show_id
        seat_ids = list(set(payload.seat_ids))
        user_id = user["user_id"]

        # booking_lock_key = CacheKey.booking_lock(show_id)
        booking_gateway = BookingGateway()
        result=await booking_gateway.reserve_seats(show_id, seat_ids, user_id)
        print(f"Booking gateway reserve_seats result: {result}")
        return {
            "status": "success" if result == 1 else "error",
            "status_code": 200 if result == 1 else 409,
            "message": "Seats reserved successfully" if result == 1 else "Some seats are already reserved or booked"
        }

        # if redis:
        #     lock = await redis.set(booking_lock_key, "1", nx=True, ex=5)
        #     if not lock:
        #         return {
        #             "status": "error",
        #             "status_code": 429,
        #             "message": "Too many booking requests"
        #         }

        # try:
        #     show_res = self.show_repo.get_show(show_id)
        #     show = show_res.get("data")

        #     if not show:
        #         return {
        #             "status": "error",
        #             "status_code": 404,
        #             "message": "Show not found"
        #         }

        #     # Check Redis for existing bookings
        #     if redis:
        #         booked_key = CacheKey.booked_seats(show_id)
        #         raw = await redis.get(booked_key)
        #         booked = set(json.loads(raw)) if raw else set()

        #         for seat_id in seat_ids:
        #             if str(seat_id) in booked:
        #                 return {
        #                     "status": "error", 
        #                     "status_code": 409,
        #                     "message": f"Seat {seat_id} already booked"
        #                 }

        #             if await redis.get(CacheKey.seat_lock(show_id, seat_id)):
        #                 return {
        #                     "status": "error", 
        #                     "status_code": 409,
        #                     "message": f"Seat {seat_id} reserved"
        #                 }

        #     else:
        #         unavailable = self.repo.check_seats_taken(show_id, seat_ids)
        #         if unavailable.get("data"):
        #             return {
        #                 "status": "error",
        #                 "status_code": 409,
        #                 "message": "Seats already booked"
        #             }

        #     total_amount = float(show["price"]) * len(seat_ids)

        #     # Lock seats in Redis
        #     if redis:
        #         locked = []
        #         try:
        #             for seat_id in seat_ids:
        #                 key = CacheKey.seat_lock(show_id, seat_id)
        #                 if not await redis.set(key, user_id, nx=True, ex=settings.SEAT_LOCK_TTL):
        #                     # Release already acquired locks
        #                     for s in locked:
        #                         await redis.delete(CacheKey.seat_lock(show_id, s))
        #                     return {
        #                         "status": "error",
        #                         "status_code": 409,
        #                         "message": f"Seat {seat_id} just locked"
        #                     }
        #                 locked.append(seat_id)
        #         except Exception as e:
        #             # Release all locks on error
        #             for s in locked:
        #                 await redis.delete(CacheKey.seat_lock(show_id, s))
        #             raise

        #     # Create booking in database
        #     booking = self.repo.create_booking(
        #         user_id=user_id,
        #         show_id=show_id,
        #         seat_ids=seat_ids,
        #         amount=total_amount
        #     )

        #     # If booking creation failed, release Redis locks
        #     if booking.get("status") != "success" and redis:
        #         for seat_id in seat_ids:
        #             await redis.delete(CacheKey.seat_lock(show_id, seat_id))

        #     return booking

        # finally:
        #     if redis:
        #         await redis.delete(booking_lock_key)

    # -------------------------
    # ✅ CONFIRM BOOKING + PAYMENT (FIXED)
    # -------------------------
    async def confirm_booking(self, booking_id, user_id, wallet_name, wallet_phone, idempotency_key=None):
        redis = get_redis()

        booking = self.repo.get_booking(booking_id)

        if not booking or booking.get("data", {}).get("user_id") != user_id:
            return {"status": "error", "message": "Booking not found"}

        booking_data = booking["data"]
        
        # Check if booking is already confirmed
        if booking_data.get("status") == "CONFIRMED":
            return {
                "status": "error",
                "status_code": 400,
                "message": "Booking already confirmed"
            }
        
        # Check if booking is expired
        if booking_data.get("status") == "EXPIRED":
            return {
                "status": "error",
                "status_code": 410,
                "message": "Booking has expired"
            }
        
        # Check if booking is cancelled
        if booking_data.get("status") == "CANCELLED":
            return {
                "status": "error",
                "status_code": 400,
                "message": "Booking has been cancelled"
            }

        # Verify booking is still pending and not expired
        expires_at = booking_data.get("expires_at")
        if expires_at:
            # Parse expires_at if it's a string
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            
            # Ensure timezone-aware comparison
            current_time = datetime.now(timezone.utc)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if current_time > expires_at:
                return {
                    "status": "error",
                    "status_code": 410,
                    "message": "Booking has expired"
                }

        result = self.repo.confirm_booking_with_payment(
            booking_id=booking_id,
            amount=booking_data["total_amount"],
            wallet_name=wallet_name,
            wallet_phone=wallet_phone,
            idempotency_key=idempotency_key
        )

        # Update Redis cache on successful confirmation
        if result.get("status") == "success" and redis:
            show_id = booking_data["show_id"]
            seat_ids = booking_data["seat_ids"]

            try:
                # Add seats to booked set in Redis
                booked_key = CacheKey.booked_seats(show_id)
                raw = await redis.get(booked_key)
                booked = set(json.loads(raw)) if raw else set()
                booked.update(map(str, seat_ids))

                await redis.set(
                    CacheKey.booked_seats(show_id), 
                    json.dumps(list(booked)), 
                    ex=settings.REDIS_CACHE_TTL if hasattr(settings, 'REDIS_CACHE_TTL') else 3600
                )

                # Remove seat locks
                for seat_id in seat_ids:
                    await redis.delete(CacheKey.seat_lock(show_id, seat_id))

            except Exception as e:
                # Log error but don't fail the request
                print(f"Redis cache update failed: {e}")

        return result

    # -------------------------
    # ❌ CANCEL BOOKING (FIXED)
    # -------------------------
    async def cancel_booking(self, booking_id, user_id):
        redis = get_redis()

        booking = self.repo.get_booking(booking_id)

        if not booking or booking.get("data", {}).get("user_id") != user_id:
            return {"status": "error", "message": "Booking not found"}

        booking_data = booking["data"]
        
        # Check if booking can be cancelled
        if booking_data.get("status") == "CONFIRMED":
            # You might want to add refund logic here
            pass
        elif booking_data.get("status") == "EXPIRED":
            return {
                "status": "error",
                "status_code": 410,
                "message": "Booking already expired"
            }
        elif booking_data.get("status") == "CANCELLED":
            return {
                "status": "error",
                "status_code": 400,
                "message": "Booking already cancelled"
            }

        result =await self.repo.cancel_booking(booking_id)

        # Release Redis locks on successful cancellation
        if result.get("status") == "success" and redis:
            for seat_id in booking_data["seat_ids"]:
                await redis.delete(CacheKey.seat_lock(booking_data["show_id"], seat_id))

        return result
    async def failed_booking(self, booking_id, user_id):
        redis= get_redis()
        try:
         result =self.repo.failed_booking(booking_id,user_id)
         if result.get("status") == "success" and redis:
             booking_seats=result.get("data",{}).get("seat_ids",[])
             # invalidate Redis locks for these seats
             for seat_id in booking_seats:
                  key=CacheKey.seat_lock(result.get("data",{}).get("show_id"),seat_id)
                  await redis.delete(key)
             return {
                 "status": "success",
                 "status_code": 200,
                 "message": "Booking marked as failed and seats released"
   
             }
         else:
             return {
                 "status": "error",
                 "status_code": 400,
                 "message": result.get("message", "Failed to mark booking as failed")
             }
        except Exception as e:
            print(f"Error in failed_booking: {e}")
            return {
                "status": "error",
                "status_code": 500,
                "message": "An error occurred while marking booking as failed"
            }
        
    # -- -----------------------
    # 🔍 GET BOOKING WITH STATUS CHECK
    # -------------------------
    async def get_booking(self, booking_id, user_id):
        """Get booking details with real-time status"""
        
        booking = self.repo.get_booking(booking_id)
        
        if not booking or booking.get("data", {}).get("user_id") != user_id:
            return {"status": "error", "message": "Booking not found"}
        
        booking_data = booking["data"]
        
        # Check if pending booking has expired
        if booking_data.get("status") == "PENDING" and booking_data.get("expires_at"):
            expires_at = booking_data["expires_at"]
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            
            current_time = datetime.now(timezone.utc)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            
            if current_time > expires_at:
                # Update status to expired
                booking_data["status"] = "EXPIRED"
        
        return {
            "status": "success",
            "status_code": 200,
            "data": booking_data
        }

    # -------------------------
    # 🧹 CLEANUP EXPIRED BOOKINGS (Optional background task)
    # -------------------------
    async def cleanup_expired_bookings(self):
        """Cleanup expired pending bookings and release Redis locks"""
        redis = get_redis()
        
        # Get all expired bookings from database
        # This would require a new repository method
        # For now, just log that cleanup is needed
        print("Cleanup of expired bookings triggered")
        
        # You can implement a background task that:
        # 1. Finds all expired PENDING bookings
        # 2. Releases their Redis locks
        # 3. Updates their status to EXPIRED if not already
        
        return {"status": "success", "message": "Cleanup completed"}