import json

from app.modules.redis.booking_gateway import BookingGateway
from app.modules.shows.repository import ShowRepository
from app.modules.booking.repository import BookingRepository
from app.config.redis import get_redis
from app.config.Cache_key import CacheKey   # ✅ import your reusable class


CACHE_TTL = 300  # 5 minutes
LOCK_TTL = 5     # seconds


class ShowService:

    def __init__(self):
        self.repo = ShowRepository()
        self.booking_repo = BookingRepository()

    # -------------------------
    # 🎬 Create Show
    # -------------------------
    async def create_show(self, data):

        result = self.repo.create_show({
            "from_location": data.from_location.strip(),
            "to_location": data.to_location.strip(),
            "departure_time": data.departure_time,
            "price": data.price,
            "seat_count": data.seat_count,
            "title": data.title.strip()
        })

        if result is not None:
            try:
             await BookingGateway().delete_trips(data.from_location.strip(), data.to_location.strip())
            except Exception:
             pass

        return {
            "status": "success" if result else "error",
            "status_code": 200 if result else 500,
            "message": "Show created successfully" if result else "Failed to create show",
            "data": result
        }

    # -------------------------
    # ✏️ Update Show
    # -------------------------
    async def update_show(self, show_id, data):

        old = self.repo.get_show(show_id)
        old_data = old if old else None

        result = self.repo.update_show(show_id, data)

        if result is not None and old_data is not None:
            try:
                await BookingGateway().delete_trips(old_data["from_location"], old_data["to_location"])
                await BookingGateway().delete_trips(result["from_location"], result["to_location"])
            except Exception:
                pass
        return {
            "status": "success" if result else "error",
            "status_code": 200 if result else 500,
            "message": "Show updated successfully" if result else "Failed to update show",
            "data": result
        }

    # -------------------------
    # 🔍 List Shows
    # -------------------------
    async def list_shows(self, from_location, to_location):

         cached_result=await BookingGateway().get_trips(from_loc=str(from_location), to_loc=str(to_location))
         if cached_result is not None:
              return {
                "data": cached_result,
                "success": True,
                "message": "Trips fetched successfully",
                "status_code": 200
              }


         result = self.repo.list_shows(from_location, to_location)
         if result:
             try:
                 await BookingGateway().set_trips(from_location, to_location, result)
             except Exception:
                 pass
         return {
            "data": result,
            "success": bool(result),
            "message": "Trips fetched successfully" if result else "No trips found",
            "status_code": 200 if result else 404
         }
            
            

     

        

    # -------------------------
    # 🎫 Get Show
    # -------------------------
    async def get_show(self, show_id):
        return self.repo.get_show(show_id)

    # -------------------------
    # 💺 SEAT MAP (FULL STATUS SYSTEM)
    # -------------------------
    async def get_seat_map(self, show_id):
        # =====================================================
        # 🚀 GET FROM CACHE FIRST
        # =====================================================
        try:
            cached = await BookingGateway().get_seat_state(show_id)
           
            print("Cached seat map:", cached)  # Debug log
            if cached is not None:
                return {
                    "status": "success",
                    "status_code": 200,
                    "data": cached
                }
        except Exception:
            seat_map=self.repo.get_seats_by_show(show_id)
            seat_booked=self.booking_repo.get_booked_seats_for_show(show_id)
            seat_reserved=set()
            try:
                 seat_reserved=await BookingGateway().get_reserved_seats(show_id)
            except Exception:
                pass
            # convert set to list for JSON serialization
            seat_booked = list(seat_booked)
            try:
                await BookingGateway().set_seat_map(show_id, seat_map)
                await BookingGateway().confirm_booking(show_id, seat_booked)
            except Exception:
                pass
            seat_reserved = list(seat_reserved)
            # we need to return seat_map with status for each seat
            seat_state = []
            for seat in seat_map:
                seat_id = seat["id"]
                if seat_id in seat_booked:
                    status = "BOOKED"
                elif seat_id in seat_reserved:
                    status = "RESERVED"
                else:
                    status = "AVAILABLE"
                seat_state.append({
                    "id": seat_id,
                    "seat_label": seat["seat_label"],
                    "status": status
                })
            return {
                "status": "success",
                "status_code": 200,
                "data": seat_state
            }

            