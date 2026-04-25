from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap import lifespan
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import validation_exception_handler

app = FastAPI(
    title="Seat Booking API",
    version="1.0.0",
    lifespan=lifespan
)

# ✅ ADD THIS BLOCK
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # allow all origins
    allow_credentials=True,
    allow_methods=["*"],          # allow ALL methods including OPTIONS
    allow_headers=["*"],          # allow ALL headers
)

# exception handler
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# routers
from app.modules.auth.routes import router as auth_router
from app.modules.booking.routes import router as booking_router
from app.modules.shows.routes import router as shows_router
from app.modules.payment.routes import router as payment_router

app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(shows_router, prefix="/shows", tags=["Shows"])
app.include_router(booking_router, prefix="/booking", tags=["Booking"])
# app.include_router(payment_router, prefix="/payment", tags=["Payment"])


@app.get("/")
async def root():
    return {
        "status": "success",
        "status_code": 200,
        "message": "Welcome to the Movie Booking API!"
    }