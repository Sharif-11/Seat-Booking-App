from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import re


class CreateShowSchema(BaseModel):
    from_location: str = Field(min_length=2, max_length=100)
    to_location: str = Field(min_length=2, max_length=100)
    departure_time: datetime
    price: float
    seat_count: int = Field(gt=0, le=50)

    @field_validator("from_location", "to_location")
    def validate_location(cls, v):
        v = v.strip()
        if not re.match(r"^[A-Za-z\s]+$", v):
            raise ValueError("Invalid location format")
        return v


class UpdateShowSchema(BaseModel):
    from_location: str = Field(min_length=2, max_length=100)
    to_location: str = Field(min_length=2, max_length=100)
    departure_time: datetime
    price: float

    @field_validator("from_location", "to_location")
    def validate_location(cls, v):
        v = v.strip()
        if not re.match(r"^[A-Za-z\s]+$", v):
            raise ValueError("Invalid location format")
        return v