"""
Pydantic schemas for revamp request endpoints.
"""

from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field


class CreateRevampRequest(BaseModel):
    """Schema for creating a revamp request."""
    order_item_id: str = Field(..., description="Order item ID for the wig to revamp")
    description: str = Field(..., min_length=1, description="Description of desired changes")
    images: Optional[List[str]] = Field(None, description="List of media IDs for reference images")

