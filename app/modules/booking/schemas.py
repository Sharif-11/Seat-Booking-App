from pydantic import BaseModel, Field, validator
from typing import Literal
from typing import List


class BookingRequestSchema(BaseModel):
    show_id: int = Field(..., gt=0)
    seat_ids: List[int] = Field(..., min_items=1, max_items=10)
    idempotency_key: str = Field(..., min_length=10, max_length=100)

    @validator("seat_ids")
    def clean_seats(cls, v):
        if len(set(v)) != len(v):
            raise ValueError("Duplicate seat_ids not allowed")

        return sorted(v)

    @validator("idempotency_key")
    def sanitize_key(cls, v):
        return v.strip().lower()

# i need another schema for payment success and failure to capture provider and other details here the user will send wallet name and wallet phone number(bangladeshi) 
class PaymentResultSchema(BaseModel):
    status: Literal["SUCCESS", "FAILED"]

    wallet_name: Literal["BKASH", "NAGAD", "ROCKET"]

    wallet_phone: str = Field(..., pattern=r"^01[3-9]\d{8}$")
    idempotency_key: str = Field(..., min_length=8, max_length=100)
