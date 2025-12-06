"""Pydantic schemas for order endpoints."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal


class CreateOrderRequest(BaseModel):
    """Schema for creating a new order."""

    offer_id: str = Field(min_length=1, description="eSIM offer ID")
    amount: Optional[Decimal] = Field(None, description="Order amount (optional, can be fetched from offer)")


class UpdateOrderStatusRequest(BaseModel):
    """Schema for updating order status."""

    status: str = Field(min_length=1, description="New order status")


class OrderResponse(BaseModel):
    """Schema for order response."""

    id: str
    user_id: str
    status: str
    amount: float
    payment_ref: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


