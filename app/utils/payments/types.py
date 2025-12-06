"""
Type definitions for payment processing.

This module contains TypedDict definitions for payment-related data structures,
providing type safety and documentation for payment flows including initialization,
processing results, and webhook handling.
"""

from typing import TypedDict, Optional, NewType
from decimal import Decimal
from ...models.user import AppUser
from ...enums.payments import PaymentType, PaymentStatus

# Creates a distinct type for currency values
CurrencyDecimal = NewType('CurrencyDecimal', Decimal)


class PaymentProcessorResponse(TypedDict):
    """
    Standardized response structure for all payment processors.
    
    Attributes:
        status (str): Payment status ("success", "error", "pending")
        message (str): Human-readable message about the payment status
        payment_id (str, optional): Provider's unique payment identifier
        authorization_url (str, optional): URL for completing payment (if redirect-based)
        reference (str): Our internal payment reference
    """
    status: str  # "success" | "error" | "pending"
    message: str
    payment_id: Optional[str]  # Provider's payment/transaction ID
    authorization_url: Optional[str]  # URL for redirect-based flows
    reference: str  # Our internal reference


class PaymentVerificationResponse(TypedDict):
    """
    Standardized verification response structure.
    
    Attributes:
        status: Payment status (completed, failed, pending, etc.)
        amount: Verified payment amount
        currency: Payment currency
        provider_reference: Payment provider's transaction ID
        meta_info: Additional payment data (e.g., payment_type, product_id)
        raw_data: Original response data
    """
    status: PaymentStatus
    amount: Decimal
    currency: str
    provider_reference: str
    meta_info: dict
    raw_data: dict  # Original response data


class BaseWebhookData(TypedDict):
    """Base webhook data all events must include."""
    raw_data: dict  # Original webhook payload
    event_type: str
    provider_reference: str  # Payment provider's transaction ID

class PaymentWebhookData(BaseWebhookData):
    """
    Standardized Payment-specific webhook data structure.
    
    This is what all payment processors must return from parse_webhook_event.
    """
    status: PaymentStatus
    reference: str  # Our payment reference
    amount: Decimal
    currency: str
    gateway_response: Optional[str]  # Provider's response message
    customer_code: Optional[str]  # Provider's customer identifier

class TransferWebhookData(BaseWebhookData):
    """Transfer-specific webhook data."""
    status: str
    reference: str
    amount: Decimal
    currency: str


class PaymentInitData(TypedDict):
    """
    Data required to initialize a payment.
    
    Attributes:
        amount: Payment amount
        currency: Currency code (e.g., "NGN", "USD")
        user: User making the payment
        payment_type: Type of payment (wallet, order, subscription)
        narration: Optional payment description
        extra_meta: Optional additional metadata
    """
    amount: Decimal
    currency: str
    user: AppUser
    payment_type: PaymentType
    narration: Optional[str]
    extra_meta: Optional[dict]