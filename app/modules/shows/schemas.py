from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import re


class CreateShowSchema(BaseModel):
    title: str = Field(min_length=2, max_length=150)

    from_location: str = Field(min_length=2, max_length=100)
    to_location: str = Field(min_length=2, max_length=100)

    departure_time: datetime
    price: float
    seat_count: int = Field(gt=0, le=50)

    # -------------------------
    # 🔤 Validators
    # -------------------------
    @field_validator("title")
    def validate_title(cls, v):
        v = v.strip()
        if not re.match(r"^[A-Za-z0-9\s]+$", v):
            raise ValueError("Invalid title format")
        return v

    @field_validator("from_location", "to_location")
    def validate_location(cls, v):
        v = v.strip().lower()
        if not re.match(r"^[A-Za-z\s]+$", v):
            raise ValueError("Invalid location format")
        return v

    @field_validator("price")
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v


class UpdateShowSchema(BaseModel):
    title: str = Field(min_length=2, max_length=150)

    from_location: str = Field(min_length=2, max_length=100)
    to_location: str = Field(min_length=2, max_length=100)

    departure_time: datetime
    price: float

    # -------------------------
    # 🔤 Validators
    # -------------------------
    @field_validator("title")
    def validate_title(cls, v):
        v = v.strip()
        if not re.match(r"^[A-Za-z0-9\s]+$", v):
            raise ValueError("Invalid title format")
        return v

    @field_validator("from_location", "to_location")
    def validate_location(cls, v):
        v = v.strip().lower()
        if not re.match(r"^[A-Za-z\s]+$", v):
            raise ValueError("Invalid location format")
        return v

    @field_validator("price")
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError("Price must be greater than 0")
        return v