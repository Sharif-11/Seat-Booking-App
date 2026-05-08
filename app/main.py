from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.bootstrap import lifespan
from app.core.exceptions import validation_exception_handler
from app.modules.socket.gateway import socket_manager

from app.modules.auth.routes import router as auth_router
from app.modules.booking.routes import router as booking_router
from app.modules.shows.routes import router as shows_router

fastapi_app = FastAPI(title="Seat Booking API", version="1.0.0", lifespan=lifespan)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.add_exception_handler(RequestValidationError, validation_exception_handler)

fastapi_app.include_router(auth_router, prefix="/auth", tags=["Auth"])
fastapi_app.include_router(shows_router, prefix="/shows", tags=["Shows"])
fastapi_app.include_router(booking_router, prefix="/booking", tags=["Booking"])

@fastapi_app.get("/")
async def root():
    return {"status": "success", "message": "Welcome to the Movie Booking API!"}

# ✅ Wrap FastAPI with Socket.IO — this becomes the actual ASGI app
app = socket_manager.build_app(fastapi_app)