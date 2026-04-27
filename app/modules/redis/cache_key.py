class CacheKey:
    PREFIX = "seat_booking_app"
    VERSION = "v1"

    @classmethod
    def _base(cls, *parts):
        return ":".join([cls.PREFIX, cls.VERSION, *map(str, parts)])

    @classmethod
    def shows(cls, from_location: str, to_location: str):
        return cls._base("shows", from_location.strip().lower(), to_location.strip().lower())

    @classmethod
    def seat_map(cls, show_id: int):
        return cls._base("seat_map", show_id)

    @classmethod
    def booked_seats(cls, show_id: int):
        return cls._base("seat_booked", show_id)

    @classmethod
    def reserved_seats(cls, show_id: int):
        return cls._base("seat_reserved", show_id)

    @classmethod
    def seat_lock(cls, show_id: int, seat_id: int):
        return cls._base("seat_lock", show_id, seat_id)