async def get_seat_state(show_id: int) -> list[dict]:
    """
    Returns the current seat state for a show.
    Each item: { id, seat_label, status: AVAILABLE | RESERVED | BOOKED }
    """
    from app.modules.redis.booking_gateway import BookingGateway
    from app.modules.booking.repository import BookingRepository
    from app.modules.shows.repository import ShowRepository

    booking_repo = BookingRepository()
    show_repo = ShowRepository()
    gateway = BookingGateway()

    # 1. Try cache first
    try:
        cached = await gateway.get_seat_state(show_id)
        if cached is not None:
            return cached
    except Exception:
        pass

    # 2. Fetch from DB
    seat_map = show_repo.get_seats_by_show(show_id)
    seat_booked = set(booking_repo.get_booked_seats_for_show(show_id))

    seat_reserved: set = set()
    try:
        seat_reserved = await gateway.get_reserved_seats(show_id)
    except Exception:
        pass

    # 3. Warm cache
    try:
        await gateway.set_seat_map(show_id, seat_map)
        await gateway.confirm_booking(show_id, list(seat_booked))
    except Exception:
        pass

    # 4. Build and return state
    return [
        {
            "id": seat["id"],
            "seat_label": seat["seat_label"],
            "status": (
                "BOOKED"     if seat["id"] in seat_booked    else
                "RESERVED"   if seat["id"] in seat_reserved  else
                "AVAILABLE"
            ),
        }
        for seat in seat_map
    ]