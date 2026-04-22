from app.modules.shows.service import ShowService


class ShowController:
    def __init__(self):
        self.service = ShowService()

    def create_show(self, payload):
        return self.service.create_show(payload)

    def update_show(self, show_id, payload):
        return self.service.update_show(show_id, payload)

    def list_shows(self, from_location, to_location):
        return self.service.list_shows(from_location, to_location)

    def get_seat_map(self, show_id):
        return self.service.get_seat_map(show_id)