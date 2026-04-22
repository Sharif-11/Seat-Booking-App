from app.modules.shows.repository import ShowRepository


class ShowService:
    def __init__(self):
        self.repo = ShowRepository()

    def create_show(self, data):
        return self.repo.create_show({
            "from_location": data.from_location.strip(),
            "to_location": data.to_location.strip(),
            "departure_time": data.departure_time,
            "price": data.price,
            "seat_count": data.seat_count
        })

    def update_show(self, show_id, data):
        return self.repo.update_show(show_id, data)

    def list_shows(self, from_location, to_location):
        return self.repo.list_shows(from_location, to_location)

    def get_seat_map(self, show_id):
        return self.repo.get_seats_by_show(show_id)