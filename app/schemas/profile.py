from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UpdateProfileRequest(BaseModel):
    """Schema for updating user profile."""
    firstname: Optional[str] = Field(None, min_length=1, max_length=200, description="User's first name")
    lastname: Optional[str] = Field(None, min_length=1, max_length=200, description="User's last name")
    gender: Optional[str] = Field(None, max_length=50, description="User's gender")
    phone: Optional[str] = Field(None, max_length=120, description="User's phone number")
    country: Optional[str] = Field(None, max_length=50, description="User's country")
    state: Optional[str] = Field(None, max_length=50, description="User's state")
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="Username (must be unique)")

