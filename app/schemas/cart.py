"""
Pydantic schemas for cart-related endpoints.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class AddCartItemRequest(BaseModel):
    """Schema for adding an item to cart."""
    variant_id: str = Field(..., description="Product variant ID")
    quantity: int = Field(..., gt=0, description="Quantity to add")
    guest_token: Optional[str] = Field(None, description="Guest cart token (for unauthenticated users)")


class UpdateCartItemRequest(BaseModel):
    """Schema for updating a cart item."""
    quantity: int = Field(..., gt=0, description="New quantity")


class ApplyPointsRequest(BaseModel):
    """Schema for applying loyalty points to cart."""
    points_to_redeem: int = Field(..., ge=500, description="Points to redeem (minimum 500)")
    guest_token: Optional[str] = Field(None, description="Guest cart token (for unauthenticated users)")




