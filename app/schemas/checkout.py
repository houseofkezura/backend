"""
Pydantic schemas for checkout endpoints.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class ShippingAddressRequest(BaseModel):
    """Schema for shipping address."""
    full_name: str = Field(..., min_length=1, description="Full name")
    phone: str = Field(..., min_length=1, description="Phone number")
    line1: str = Field(..., min_length=1, description="Address line 1")
    line2: Optional[str] = Field(None, description="Address line 2")
    city: str = Field(..., min_length=1, description="City")
    state: str = Field(..., min_length=1, description="State/Province")
    postal_code: str = Field(..., min_length=1, description="Postal code")
    country: str = Field(..., min_length=2, max_length=2, description="Country code (e.g., NG)")


class CheckoutRequest(BaseModel):
    """Schema for checkout request."""
    cart_id: Optional[str] = Field(None, description="Cart ID (for authenticated users)")
    guest_token: Optional[str] = Field(None, description="Guest cart token (for unauthenticated users)")
    shipping_address: ShippingAddressRequest = Field(..., description="Shipping address")
    shipping_method: Optional[str] = Field("standard", description="Shipping method (standard/express)")
    payment_method: str = Field("card", description="Payment method")
    payment_token: Optional[str] = Field(None, description="Payment token from payment gateway")
    apply_points: bool = Field(False, description="Whether to apply loyalty points")
    points_to_redeem: int = Field(0, ge=0, description="Points to redeem")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key for duplicate request prevention")
    # Guest checkout fields
    email: Optional[EmailStr] = Field(None, description="Email (required for guest checkout)")
    phone: Optional[str] = Field(None, description="Phone number (required for guest checkout)")
    first_name: Optional[str] = Field(None, description="First name (for guest checkout)")
    last_name: Optional[str] = Field(None, description="Last name (for guest checkout)")

