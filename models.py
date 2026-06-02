from __future__ import annotations

import re
from pydantic import BaseModel, EmailStr, Field, validator


class Address(BaseModel):
    city: str = Field(..., min_length=1)
    pincode: str = Field(..., min_length=5, max_length=10)

    @validator("city")
    def clean_city(cls, value: str) -> str:
        return value.strip()

    @validator("pincode")
    def validate_pincode(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) < 5 or len(digits) > 10:
            raise ValueError("pincode must contain 5 to 10 digits")
        return digits


class ContactCard(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    phone: str
    address: Address

    @validator("name")
    def clean_name(cls, value: str) -> str:
        return value.strip()

    @validator("phone")
    def validate_phone(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if len(digits) != 10:
            raise ValueError("phone must contain exactly 10 digits")
        return digits
