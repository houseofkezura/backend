"""Pydantic schemas for payment endpoints."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal


class InitPaymentRequest(BaseModel):
    """Schema for payment initialization request."""

    amount: Decimal = Field(description="Payment amount")
    description: Optional[str] = Field(None, description="Payment description")
    currency: Optional[str] = Field("USD", description="Payment currency code")

class VerifyPaymentRequest(BaseModel):
    """Schema for payment verification request."""

    reference: str = Field(description="Payment reference")

class CheckoutRequest(BaseModel):
    """Schema for payment checkout request."""

    order_id: Optional[str] = Field(None, description="Order ID (if order already exists)")
    offer_id: Optional[str] = Field(None, description="Offer ID (if creating order on checkout)")
    amount: Decimal = Field(description="Payment amount")
    currency: Optional[str] = Field("USD", description="Payment currency code")


class CheckoutResponse(BaseModel):
    """Schema for payment checkout response."""

    payment_url: str = Field(description="Payment gateway URL for redirect")
    reference: str = Field(description="Payment reference/transaction ID")
    order_id: Optional[str] = Field(None, description="Associated order ID")


class PaymentStatusResponse(BaseModel):
    """Schema for payment status response."""

    reference: str = Field(description="Payment reference")
    status: str = Field(description="Payment status")
    amount: Decimal = Field(description="Payment amount")
    currency: str = Field(description="Payment currency")
    order_id: Optional[str] = Field(None, description="Associated order ID")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


