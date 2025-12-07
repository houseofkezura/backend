"""
Pydantic schemas for address management endpoints.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class CreateAddressRequest(BaseModel):
    """Schema for creating an address."""
    state: str = Field(..., min_length=1, description="State/Province")
    country: str = Field(..., min_length=2, max_length=2, description="Country code (e.g., NG)")


class UpdateAddressRequest(BaseModel):
    """Schema for updating an address."""
    state: Optional[str] = Field(None, min_length=1)
    country: Optional[str] = Field(None, min_length=2, max_length=2)

