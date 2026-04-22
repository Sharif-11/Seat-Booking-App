from fastapi import APIRouter
from app.modules.shows.controller import ShowController
from app.modules.shows.schemas import CreateShowSchema, UpdateShowSchema

router = APIRouter()
controller = ShowController()


@router.post("/create")
def create_show(payload: CreateShowSchema):
    return controller.create_show(payload)


@router.put("/update/{show_id}")
def update_show(show_id: int, payload: UpdateShowSchema):
    return controller.update_show(show_id, payload)


@router.get("/list")
def list_shows(from_location: str = None, to_location: str = None):
    return controller.list_shows(from_location, to_location)


@router.get("/{show_id}/seats")
def get_seat_map(show_id: int):
    return controller.get_seat_map(show_id)