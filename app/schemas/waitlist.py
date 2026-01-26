"""
Pydantic schemas for waitlist endpoints.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class CreateWaitlistEntryRequest(BaseModel):
    """Schema for joining the waitlist."""
    email: EmailStr = Field(..., description="Email address to join waitlist")


class UpdateWaitlistStatusRequest(BaseModel):
    """Schema for updating waitlist entry status."""
    status: Optional[str] = Field(None, min_length=1, description="New status (pending, invited, converted)")
