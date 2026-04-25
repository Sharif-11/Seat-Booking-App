class CacheKey:
    PREFIX = "seat_booking"   # 🔥 global namespace
    VERSION = "v1"            # 🔥 for future invalidation

    # ---------------- BASE ----------------
    @classmethod
    def _base(cls, *parts):
        return ":".join([cls.PREFIX, cls.VERSION, *map(str, parts)])

    # ---------------- SHOWS ----------------
    @classmethod
    def shows(cls, from_location: str, to_location: str):
        return cls._base(
            "shows",
            from_location.strip().lower(),
            to_location.strip().lower()
        )

    # ---------------- SEATS ----------------
    @classmethod
    def seats(cls, show_id: int):
        return cls._base("seats", show_id)

    # ---------------- BOOKED SEATS ----------------
    @classmethod
    def booked_seats(cls, show_id: int):
        return cls._base("seat_booked", show_id)

    # ---------------- SEAT LOCK ----------------
    @classmethod
    def seat_lock(cls, show_id: int, seat_id: int):
        return cls._base("seat_lock", show_id, seat_id)
    @classmethod
    def booking_lock(cls, show_id: int):
        return cls._base("booking_lock", show_id)
    
    @classmethod
    def booking_idempotency(cls, user_id, show_id, key):
        return cls._base("booking_idempotency", user_id, show_id, key)