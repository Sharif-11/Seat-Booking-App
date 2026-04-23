from app.modules.shows.service import ShowService


class ShowController:
    def __init__(self):
        self.service = ShowService()

    async def create_show(self, payload):
        return await self.service.create_show(payload)

    async def update_show(self, show_id, payload):
        return await self.service.update_show(show_id, payload)

    async def list_shows(self, from_location, to_location):
        return await self.service.list_shows(from_location, to_location)

    async def get_seat_map(self, show_id):
        return await self.service.get_seat_map(show_id)