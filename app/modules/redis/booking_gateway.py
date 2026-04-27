import json
from app.modules.redis.redis_repository import RedisRepository
from app.modules.redis.redis_connection import get_redis
from app.modules.redis.cache_key import CacheKey

class SeatStateError(Exception):
    pass

class BookingGateway:
    """
    🚀 SINGLE ENTRY POINT FOR ENTIRE SYSTEM
    No Redis knowledge outside this class.
    """

    # ---------------- TTL CONFIG ----------------
    _TRIP_TTL = 3600
    _SEAT_MAP_TTL = 3600
    _RESERVATION_TTL = 120
    _BOOKED_TTL = 7 * 24 * 3600

    def __init__(self):
        self.repo = RedisRepository()

    # =====================================================
    # 🔥 LUA SEAT RESERVATION (ATOMIC)
    # =====================================================
  
    _RESERVE_LUA = """
    for i=1,#KEYS do
        if redis.call("EXISTS", KEYS[i]) == 1 then
            return 0
        end
    end

    for i=1,#KEYS do
        redis.call("SET", KEYS[i], ARGV[1], "EX", ARGV[2])
    end

    local reserved = "seat_booking_app:v1:seat_reserved:" .. ARGV[3]

    for i=1,#KEYS do
        local seat = string.match(KEYS[i], ":(%d+)$")
        redis.call("SADD", reserved, seat)
    end

    return 1
    """

    async def reserve_seats(self, show_id: int, seats: list[int], user_id: str):
        keys = [CacheKey.seat_lock(show_id, s) for s in seats]
        script = self.repo.script(self._RESERVE_LUA)

        return await script(
            keys=keys,
            args=[user_id, self._RESERVATION_TTL, show_id]
        )

    # =====================================================
    # 💳 CONFIRM BOOKING
    # =====================================================
    async def confirm_booking(self, show_id: int, seats: list[int]):
        pipe = self.repo.pipeline()

        pipe.sadd(CacheKey.booked_seats(show_id), *seats)
        pipe.expire(CacheKey.booked_seats(show_id), self._BOOKED_TTL)

        pipe.srem(CacheKey.reserved_seats(show_id), *seats)

        for s in seats:
            pipe.delete(CacheKey.seat_lock(show_id, s))

        await pipe.execute()

    # =====================================================
    # ❌ CANCEL BOOKING
    # =====================================================
    async def cancel_booking(self, show_id: int, seats: list[int]):
        pipe = self.repo.pipeline()

        pipe.srem(CacheKey.reserved_seats(show_id), *seats)

        for s in seats:
            pipe.delete(CacheKey.seat_lock(show_id, s))

        await pipe.execute()

    # =====================================================
    # 📊 SEAT STATE (UI)
    # =====================================================
  

    
    async def get_seat_state(self, show_id: int):
    
        redis = self.repo.redis
    
        # -------------------------------
        # 1. LOAD SEAT MAP (MANDATORY)
        # -------------------------------
        seat_map = await self.get_seat_map(show_id)
    
        if seat_map is None:
            raise SeatStateError(f"Seat map cache missing for show_id={show_id}")
    
        # -------------------------------
        # 2. CHECK BOOKED KEY EXISTS
        # -------------------------------
        booked_key = CacheKey.booked_seats(show_id)
    
        exists = await redis.exists(booked_key)
        if not exists:
            raise SeatStateError(f"Booked seat cache missing for show_id={show_id}")
    
        booked_raw = await self.repo.smembers(booked_key)
        booked = set(map(int, booked_raw)) if booked_raw else set()
        reserved = await self.get_reserved_seats(show_id)
    
        # -------------------------------
        # 4. BUILD FINAL STATE
        # -------------------------------
        seat_state = []
    
        for seat in seat_map:
            seat_id = seat["id"]
    
            if seat_id in booked:
                status = "BOOKED"
            elif seat_id in reserved:
                status = "RESERVED"
            else:
                status = "AVAILABLE"
    
            seat_state.append({
                "id": seat_id,
                "seat_label": seat["seat_label"],
                "status": status
            })
    
        return seat_state
    
        # =====================================================
        # 🚀 TRIP CACHE (FULL ABSTRACTION)
        # =====================================================
    async def get_reserved_seats(self, show_id: int):
        # calculate reserved seats by scanning locks
        redis = self.repo.redis
        pattern = CacheKey._base("seat_lock", show_id, "*")
        cursor = 0
        reserved = []
        try:
            while True:
                cursor, keys = await redis.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                reserved.extend([
                    int(key.split(":")[-1])
                    for key in keys
                ])
                if cursor == 0:
                    break
        except Exception as e:
            raise SeatStateError(f"Failed to scan reserved seats: {str(e)}")
        # convert each item to int and return as set
        reserved = [int(x) for x in reserved]
        return set(reserved)
    async def get_trips(self, from_loc: str, to_loc: str):
        key = CacheKey.shows(from_loc, to_loc)
        data = await self.repo.get(key)
        return json.loads(data) if data else None

    async def set_trips(self, from_loc: str, to_loc: str, data):
        key = CacheKey.shows(from_loc, to_loc)
        return await self.repo.set(key, json.dumps(data), ex=self._TRIP_TTL)
    async def delete_trips(self, from_loc: str, to_loc: str):
        key = CacheKey.shows(from_loc, to_loc)
        return await self.repo.delete(key)

    # =====================================================
    # 🪑 SEAT MAP CACHE
    # =====================================================
    async def get_seat_map(self, show_id: int):
        key = CacheKey.seat_map(show_id)
        data = await self.repo.get(key)
        return json.loads(data) if data else None

    async def set_seat_map(self, show_id: int, data):
        key = CacheKey.seat_map(show_id)
        return await self.repo.set(key, json.dumps(data), ex=self._SEAT_MAP_TTL)