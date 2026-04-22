from pydantic import BaseModel, Field, field_validator
import re


class RequestOTPInput(BaseModel):
    phone: str = Field(...)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        v = v.strip()

        # Bangladesh 11-digit validation: 01XXXXXXXXX
        if not re.fullmatch(r"01[3-9]\d{8}", v):
            raise ValueError("Invalid Bangladeshi phone number")

        return v


class VerifyOTPInput(BaseModel):
    phone: str = Field(...)
    otp: str = Field(...)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        v = v.strip()
        if not re.fullmatch(r"01[3-9]\d{8}", v):
            raise ValueError("Invalid Bangladeshi phone number")
        return v

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v):
        if not re.fullmatch(r"\d{6}", v):
            raise ValueError("OTP must be 6 digits")
        return v