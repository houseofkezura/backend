"""
Pydantic schemas for CRM-related endpoints.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class CreateRatingRequest(BaseModel):
    """Schema for creating a CRM staff rating."""
    order_id: str = Field(..., description="Order ID")
    stars: int = Field(..., ge=1, le=5, description="Rating (1-5 stars)")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional comment")






