"""
Pydantic schemas for product material endpoints.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class CreateMaterialRequest(BaseModel):
    """Schema for creating a product material."""
    name: str = Field(..., min_length=1, max_length=255, description="Material name (unique)")
    description: Optional[str] = Field(None, description="Material description")


class UpdateMaterialRequest(BaseModel):
    """Schema for updating a product material."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Material name")
    description: Optional[str] = Field(None, description="Material description")
