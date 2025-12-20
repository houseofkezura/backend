"""
Pydantic schemas for wishlist-related endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class AddWishlistItemRequest(BaseModel):
    """Schema for adding an item to wishlist."""
    variant_id: str = Field(..., description="Product variant ID to add to wishlist")


