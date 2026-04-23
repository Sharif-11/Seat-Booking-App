import json
import asyncio

from app.modules.shows.repository import ShowRepository
from app.config.redis import get_redis


CACHE_TTL = 300  # 5 minutes
LOCK_TTL = 5     # seconds


class ShowService:

    def __init__(self):
        self.repo = ShowRepository()

    # -------------------------
    # 🔑 Cache Keys
    # -------------------------
    def _cache_key(self, from_location: str, to_location: str):
        return f"shows:{from_location.strip().lower()}:{to_location.strip().lower()}"

    def _seat_cache_key(self, show_id: int):
        return f"seats:{show_id}"

    def _booked_cache_key(self, show_id: int):
        return f"seat_booked:{show_id}"

    def _seat_lock_key(self, show_id: int, seat_id: int):
        return f"seat_lock:{show_id}:{seat_id}"

    # -------------------------
    # 🎬 Create Show
    # -------------------------
    async def create_show(self, data):

        result = self.repo.create_show({
            "from_location": data.from_location.strip(),
            "to_location": data.to_location.strip(),
            "departure_time": data.departure_time,
            "price": data.price,
            "seat_count": data.seat_count
        })

        redis = get_redis()
        if redis:
            try:
                await redis.delete(self._cache_key(data.from_location, data.to_location))
            except Exception:
                pass

        return result

    # -------------------------
    # ✏️ Update Show
    # -------------------------
    async def update_show(self, show_id, data):

        old = self.repo.get_show(show_id)
        old_data = old.get("data") if old else None

        result = self.repo.update_show(show_id, data)

        if old_data:
            redis = get_redis()
            if redis:
                try:
                    await redis.delete(
                        self._cache_key(
                            old_data["from_location"],
                            old_data["to_location"]
                        )
                    )
                except Exception:
                    pass

        return result

    # -------------------------
    # 🔍 List Shows
    # -------------------------
    async def list_shows(self, from_location, to_location):

        key = self._cache_key(from_location, to_location)
        redis = get_redis()

        if redis:
            try:
                cached = await redis.get(key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass

        result = self.repo.list_shows(from_location, to_location)

        if redis:
            try:
                await redis.set(key, json.dumps(result), ex=CACHE_TTL)
            except Exception:
                pass

        return result

    # -------------------------
    # 🎫 Get Show
    # -------------------------
    async def get_show(self, show_id):
        return self.repo.get_show(show_id)

    # -------------------------
    # 💺 SEAT MAP (FULL STATUS SYSTEM)
    # -------------------------
    async def get_seat_map(self, show_id):

        redis = get_redis()

        base_key = self._seat_cache_key(show_id)
        booked_key = self._booked_cache_key(show_id)

        # -------------------------
        # 1️⃣ Load seats
        # -------------------------
        if redis:
            try:
                cached = await redis.get(base_key)

                if cached:
                    seat_map = json.loads(cached)
                else:
                    seat_map = self.repo.get_seats_by_show(show_id)
                    await redis.set(base_key, json.dumps(seat_map), ex=CACHE_TTL)

            except Exception:
                seat_map = self.repo.get_seats_by_show(show_id)
        else:
            seat_map = self.repo.get_seats_by_show(show_id)

        seats = seat_map.get("data", [])

        # -------------------------
        # 2️⃣ BOOKED (Redis - CONFIRMED bookings only)
        # -------------------------
        booked = set()

        if redis:
            try:
                raw = await redis.get(booked_key)
                if raw:
                    booked = set(map(str, json.loads(raw)))
            except Exception:
                pass

        # -------------------------
        # 3️⃣ RESERVED (seat locks - temporary holds)
        # -------------------------
        reserved = set()

        if redis:
            try:
                for seat in seats:
                    seat_id = seat["id"]
                    key = self._seat_lock_key(show_id, seat_id)

                    if await redis.get(key):
                        reserved.add(str(seat_id))
            except Exception:
                pass

        # -------------------------
        # 4️⃣ PENDING (DB - should be treated as RESERVED)
        # -------------------------
        pending_seats = set()

        try:
            db_pending = self.repo.get_pending_seats(show_id)
            if db_pending and db_pending.get("data"):
                pending_seats = set(map(str, db_pending["data"]))
        except Exception:
            pass

        # -------------------------
        # 5️⃣ Merge status (PENDING → RESERVED)
        # -------------------------
        for seat in seats:
            sid = str(seat["id"])

            if sid in booked:
                seat["status"] = "BOOKED"
            elif sid in reserved or sid in pending_seats:
                seat["status"] = "RESERVED"
            else:
                seat["status"] = "AVAILABLE"

        return seat_map