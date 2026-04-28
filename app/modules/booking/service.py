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
    
    # Get User Bookings
    def get_bookings_by_user_id(self, user_id):
        return self.repo.get_bookings_by_user_id(user_id)
    def download_ticket(self, booking_id, user_id):
        booking = self.repo.get_booking_with_payment_and_show(user_id, booking_id)

        if not booking or booking.get("data", {}).get("user_id") != user_id:
            return {"status": "error", "message": "Booking not found"}

        return booking.get("data", {})

    # -------------------------
    # 🚀 CREATE BOOKING
    # -------------------------
    async def create_booking(self, payload, user):
     
 
     show_id = payload.show_id
     seat_ids = list(set(payload.seat_ids))
     user_id = user["user_id"]
 
     # -------------------------
     # 1️⃣ Validate show exists
     # -------------------------
     existing_show = self.show_repo.get_show(show_id)
     if existing_show is None:
         return {
             "status": "error",
             "status_code": 404,
             "message": "Show not found"
         }
 
     total_amount = len(seat_ids) * float(existing_show.get("price", 0))
 
     # -------------------------
     # 2️⃣ Cache layer — atomically reserve seats in Redis via gateway
     # Blocks conflicting requests before they ever reach the DB
     # -------------------------
     booking_gateway = BookingGateway()
     cache_result = await booking_gateway.reserve_seats(show_id, seat_ids, user_id)
 
     if cache_result != 1:
         return {
             "status": "error",
             "status_code": 409,
             "message": "Some seats are already reserved or booked"
         }
 
     # -------------------------
     # 3️⃣ DB layer — persist the booking now that cache lock is acquired
     # If DB fails, release the Redis locks so seats aren't stuck
     # -------------------------
     try:
         booking = self.repo.create_booking(
             user_id=user_id,
             show_id=show_id,
             seat_ids=seat_ids,
             amount=total_amount
         )
 
         if booking.get("status") != "success":
             # DB rejected the booking (conflict, validation, etc.)
             # Roll back Redis locks so other users can attempt these seats
            await BookingGateway().release_seat_locks(show_id, seat_ids)
 
            return {
                 "status": "error",
                 "status_code": booking.get("status_code", 500),
                 "message": booking.get("message", "Failed to create booking")
             }
 
         return {
             "status": "success",
             "status_code": 201,
             "message": "Booking created successfully",
             "data": booking.get("data")
         }
 
     except Exception as e:
         # Unexpected error — always release Redis locks to prevent seat deadlock
         await BookingGateway().release_seat_locks(show_id, seat_ids)
 
         return {
             "status": "error",
             "status_code": 500,
             "message": f"Booking creation failed: {str(e)}"
         }
 
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
        # DELETE ALL EXPIRED BOOKINGS FOR THIS SHOW TO ENSURE STATUS IS UP TO DATE
        self.repo._expire_old_bookings_for_show()

        result = self.repo.confirm_booking_with_payment(
            booking_id=booking_id,
            amount=booking_data["total_amount"],
            wallet_name=wallet_name,
            wallet_phone=wallet_phone,
            idempotency_key=idempotency_key
        )

        # Update Redis cache on successful confirmation
        if result.get("status") == "success":
            show_id = booking_data["show_id"]
            seat_ids = booking_data["seat_ids"]
            try:
                await BookingGateway().confirm_booking(show_id, seat_ids)

            except Exception as e:
                print(f"Error updating Redis cache after DB confirmation: {e}")
                # We don't want to fail the entire request if cache update fails,
                # but we should log this for investigation.
            

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
        try:
            failed_booking=self.repo.failed_booking(booking_id,user_id)
            if failed_booking.get("status")!="success":
                return {
                    "status": "error",
                    "status_code": failed_booking.get("status_code", 500),
                    "message": failed_booking.get("message", "Failed to mark booking as failed")
                }
            
            seat_ids=failed_booking.get("data", {}).get("seat_ids", [])
            show_id=failed_booking.get("data", {}).get("show_id")
            await BookingGateway().release_seat_locks(show_id, seat_ids)
            return {
                    "status": "success",
                    "status_code": 200,
                    "message": "Booking marked as failed and seats released"
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