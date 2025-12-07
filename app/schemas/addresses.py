"""
Pydantic schemas for address management endpoints.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class CreateAddressRequest(BaseModel):
    """Schema for creating an address."""
    label: Optional[str] = Field(None, max_length=100, description="Address label (e.g., 'Home', 'Work')")
    line1: str = Field(..., min_length=1, description="Address line 1")
    line2: Optional[str] = Field(None, description="Address line 2")
    city: str = Field(..., min_length=1, description="City")
    state: str = Field(..., min_length=1, description="State/Province")
    postal_code: str = Field(..., min_length=1, description="Postal code")
    country: str = Field(..., min_length=2, max_length=2, description="Country code (e.g., NG)")
    is_default: bool = Field(False, description="Set as default address")


class UpdateAddressRequest(BaseModel):
    """Schema for updating an address."""
    label: Optional[str] = Field(None, max_length=100)
    line1: Optional[str] = Field(None, min_length=1)
    line2: Optional[str] = None
    city: Optional[str] = Field(None, min_length=1)
    state: Optional[str] = Field(None, min_length=1)
    postal_code: Optional[str] = Field(None, min_length=1)
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    is_default: Optional[bool] = None

