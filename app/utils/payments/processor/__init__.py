from enum import Enum
from decimal import Decimal
from typing import TypedDict, Optional, Set, Any
from ...helpers.basics import generate_random_string
from ....enums.payments import PaymentStatus
from ..types import PaymentWebhookData, TransferWebhookData

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
    """
    status: PaymentStatus
    amount: Decimal
    currency: str
    provider_reference: str
    meta_info: dict

class PaymentProcessor:
    """
    Base class for payment processors.
    """
    reference_prefix = "pay_"  # Default prefix
    supported_currencies: Set[str] = {"USD"}  # Default, override in subclasses
    
    def __init__(self, secret_key: str = "", public_key: str = "", api_key: str = ""):
        self.secret_key = secret_key
        self.public_key = public_key
        self.api_key = api_key
        self.secret_hash = "42cf4e6d9d8c728003ae3361d5268c23"
        self.reference = f"{self.reference_prefix}{generate_random_string(10)}"
    
    def supports_currency(self, currency: str) -> bool:
        """
        Check if the processor supports a given currency.
        
        Args:
            currency (str): Currency code to check (e.g., "NGN", "USD")
            
        Returns:
            bool: True if currency is supported, False otherwise
        """
        return currency.upper() in self.supported_currencies

    def initialize_payment(self, amount: float | Decimal, currency: str, customer_data: dict, redirect_url: Optional[str] = None) -> PaymentProcessorResponse:
        """
        Abstract method for processing payments.
        Must be implemented by subclasses.
        
        Returns:
            dict: {
                "status": "success" | "failed",
                "message": str,
                "transaction_id": str | None,
                "redirect_url": str | None (if applicable)
            }
        """
        raise NotImplementedError("Subclasses must implement this method.")
    
    def verify_payment(self, payment_reference: str) -> PaymentVerificationResponse:
        """Verify payment status with provider."""
        raise NotImplementedError("Subclasses must implement this method.")
    
    def verify_webhook_signature(self, payload: dict = None, signature: str | None = None) -> bool:
        """Verify webhook signature."""
        raise NotImplementedError("Subclasses must implement this method.")
    
    def parse_webhook_event(self, payload: dict) -> PaymentWebhookData | TransferWebhookData:
        """Parse webhook payload into standard format."""
        raise NotImplementedError("Subclasses must implement this method.")
