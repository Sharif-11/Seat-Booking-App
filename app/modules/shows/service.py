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
    # 🔑 Cache Key Builder
    # -------------------------
    def _cache_key(self, from_location: str, to_location: str) -> str:
        return f"shows:{from_location.strip().lower()}:{to_location.strip().lower()}"

    def _seat_cache_key(self, show_id: int) -> str:
        return f"seats:{show_id}"

    # -------------------------
    # 🧹 Cache Invalidation
    # -------------------------
    async def _invalidate_search_cache(self, from_location: str, to_location: str):
        redis = get_redis()
        if not redis:
            return

        try:
            await redis.delete(self._cache_key(from_location, to_location))
        except Exception:
            pass

    async def _invalidate_seat_cache(self, show_id: int):
        redis = get_redis()
        if not redis:
            return

        try:
            await redis.delete(self._seat_cache_key(show_id))
        except Exception:
            pass

    # -------------------------
    # 🎬 Create Show
    # -------------------------
    async def create_show(self, data):
        result = await self.repo.create_show({
            "from_location": data.from_location.strip(),
            "to_location": data.to_location.strip(),
            "departure_time": data.departure_time,
            "price": data.price,
            "seat_count": data.seat_count
        })

        await self._invalidate_search_cache(
            data.from_location,
            data.to_location
        )

        return result

    # -------------------------
    # ✏️ Update Show
    # -------------------------
    async def update_show(self, show_id, data):
        old_show_res = await self.repo.get_show(show_id)
        old_show = old_show_res.get("data") if old_show_res else None

        result = await self.repo.update_show(show_id, data)

        # invalidate old cache
        if old_show:
            await self._invalidate_search_cache(
                old_show["from_location"],
                old_show["to_location"]
            )

        # invalidate new cache
        await self._invalidate_search_cache(
            getattr(data, "from_location", old_show["from_location"]),
            getattr(data, "to_location", old_show["to_location"])
        )

        return result

    # -------------------------
    # 🔍 List Shows (Cache Aside + Lock)
    # -------------------------
    async def list_shows(self, from_location: str, to_location: str):
        key = self._cache_key(from_location, to_location)
        redis = get_redis()

        # fallback if redis not available
        if not redis:
            return await self.repo.list_shows(from_location, to_location)

        # 1️⃣ cache lookup
        try:
            cached = await redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            return await self.repo.list_shows(from_location, to_location)

        lock_key = f"lock:{key}"

        # 2️⃣ lock
        try:
            lock_acquired = await redis.set(lock_key, "1", nx=True, ex=LOCK_TTL)
        except Exception:
            lock_acquired = False

        if lock_acquired:
            try:
                result = await self.repo.list_shows(from_location, to_location)

                await redis.set(
                    key,
                    json.dumps(result),
                    ex=CACHE_TTL
                )

                return result

            finally:
                try:
                    await redis.delete(lock_key)
                except Exception:
                    pass

        # 3️⃣ wait retry
        await asyncio.sleep(0.05)

        try:
            cached = await redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

        return await self.repo.list_shows(from_location, to_location)

    # -------------------------
    # 🎫 Get Single Show (cached optional later)
    # -------------------------
    async def get_show(self, show_id):
        return await self.repo.get_show(show_id)

    # -------------------------
    # 💺 Seat Map (WITH CACHE FIX)
    # -------------------------
    async def get_seat_map(self, show_id):
        key = self._seat_cache_key(show_id)
        redis = get_redis()

        if not redis:
            return await self.repo.get_seats_by_show(show_id)

        try:
            cached = await redis.get(key)
            if cached:
                return json.loads(cached)
        except Exception:
            return await self.repo.get_seats_by_show(show_id)

        result = await self.repo.get_seats_by_show(show_id)

        try:
            await redis.set(key, json.dumps(result), ex=CACHE_TTL)
        except Exception:
            pass

        return result