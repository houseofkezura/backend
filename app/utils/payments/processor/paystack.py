import requests, hmac, hashlib
from decimal import Decimal
from typing import Optional, Any
from flask import request

from ....logging import log_event, log_error
from . import PaymentProcessor
from ..exceptions import SignatureError
from ..types import (
    PaymentProcessorResponse,
    PaymentVerificationResponse,
    PaymentStatus,
    PaymentWebhookData,
    TransferWebhookData,
)
from ....enums import TransferStatus

class PaystackProcessor(PaymentProcessor):
    """
    Handles payments via Paystack API.
    """
    reference_prefix = "pst_"
    supported_currencies = {"NGN", "USD", "GHS"}
    
    def initialize_payment(self, amount: float | Decimal, currency: str, customer_data: dict, redirect_url: Optional[str] = None) -> PaymentProcessorResponse:
        """
        Initialize payment with Paystack.
        
        Args:
            amount: Payment amount
            currency: Payment currency code
            customer_data: Customer information (email, name)
            
        Returns:
            PaymentProcessorResponse: Standardized payment response
        """
        # Validate email is present
        customer_email = customer_data.get("email")
        if not customer_email:
            log_error("paystack_init_failed", "Customer email is required for Paystack payments")
            return PaymentProcessorResponse(
                status="error",
                message="Customer email is required for payment",
                payment_id=None,
                authorization_url=None,
                reference=self.reference,
            )
        
        url = "https://api.paystack.co/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "email": customer_email,
            "amount": int(float(amount) * 100),  # Paystack expects amount in kobo
            "currency": currency,
            "reference": self.reference,
            "callback_url": redirect_url
        }
        
        log_event("paystack_init_request", f"Initializing payment: amount={amount}, currency={currency}, email={customer_email}")

        try:
            response = requests.post(url, json=data, headers=headers)
            response_data = response.json() or {}
            
            # Log the full response for debugging
            if not response_data.get("status"):
                log_error("paystack_init_error", f"Paystack API error: {response_data.get('message', 'Unknown error')}", extra={"response": response_data})
            else:
                log_event("paystack_init_success", f"Payment initialized: ref={self.reference}")
            
            payment_response = PaymentProcessorResponse(
                status="success" if response_data.get("status") else "error",
                message=response_data.get("message", ""),
                payment_id=response_data.get("data", {}).get("reference"),
                authorization_url=response_data.get("data", {}).get("authorization_url"),
                reference=self.reference,
            )
            return payment_response
        except Exception as e:
            log_error("paystack_init_exception", str(e), exc_info=e)
            return PaymentProcessorResponse(
                status="error",
                message=f"Payment initialization failed: {str(e)}",
                payment_id=None,
                authorization_url=None,
                reference=self.reference,
            )
    
    def verify_payment(self, payment_reference: str) -> PaymentVerificationResponse:
        """
        Verify payment status with Paystack.
        
        Args:
            payment_reference: Payment reference to verify
            
        Returns:
            dict: Verification response with standardized status
        """
        url = f"https://api.paystack.co/transaction/verify/{payment_reference}"
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response_data = response.json() or {}
        data: dict = response_data.get("data", {}) or {}
        
        status_mapping = {
            "success": PaymentStatus.COMPLETED,
            "failed": PaymentStatus.FAILED,
            "pending": PaymentStatus.PENDING,
            "abandoned": PaymentStatus.FAILED
        }
        
        status = status_mapping.get(str(data.get("status", "")), PaymentStatus.PENDING)
        amount = Decimal(str(data.get("amount", 0))) / 100
        currency = str(data.get("currency", ""))
        provider_reference = str(data.get("id", ""))
        meta_info: dict = data if isinstance(data, dict) else {}
        raw: dict = response_data if isinstance(response_data, dict) else {}

        return PaymentVerificationResponse(
            status=status,
            amount=amount,
            currency=currency,
            provider_reference=provider_reference,
            meta_info=meta_info,
            raw_data=raw,
        )
    
    def verify_webhook_signature(self, payload: Optional[dict] = None, signature: str | None = None) -> bool:
        """
        Verify Paystack webhook signature.
        
        Args:
            payload: Webhook request body (unused, kept for interface consistency)
            signature: Signature from webhook header (unused, extracted from request)
            
        Returns:
            bool: True if signature is valid
            
        Raises:
            SignatureError: If signature is missing or invalid
        """
        signature = request.headers.get('x-paystack-signature') # Get signature from the request headers
        if not signature:
            raise SignatureError("Missing webhook signature")
        
        secret_key = self.secret_key # Get secret key from settings
        
        # Create hash using the secret key and the data
        hash = hmac.new(
            secret_key.encode(),
            msg=request.data,
            digestmod=hashlib.sha512
        )
        
        
        # Verify the signature
        if not hmac.compare_digest(hash.hexdigest(), signature):
            raise SignatureError(f'Invalid Paystack signature')
        
        
        return True
    
    def parse_webhook_event(self, payload: dict) -> PaymentWebhookData | TransferWebhookData:
        """
        Parse Paystack webhook payload into standard format based on event type.
        
        Args:
            payload: Raw webhook data
            
        Returns:
            PaymentWebhookData or TransferWebhookData based on event type
        """
        event = str(payload.get("event", ""))
        
        if event.startswith("charge."):
            return self._parse_payment_webhook(payload)
        elif event.startswith("transfer."):
            return self._parse_transfer_webhook(payload)
        else:
            raise ValueError(f"Unsupported webhook event: {event}")

    
    def _parse_payment_webhook(self, payload: dict) -> PaymentWebhookData:
        """Parse payment-specific webhook data."""
        event = str(payload.get("event", ""))
        data = payload.get("data", {})
        transaction_status = data.get("status", "").lower()
        
        payment_status = self._determine_payment_status(event, transaction_status)
        
        parsed_data = PaymentWebhookData(
            event_type="payment",
            status=payment_status,
            reference=data.get("reference", ""),
            provider_reference=str(data.get("id", "")),
            amount=Decimal(str(data.get("amount", 0))) / 100,
            currency=data.get("currency", ""),
            raw_data=payload,
            gateway_response=data.get("gateway_response"),
            customer_code=data.get("customer", {}).get("customer_code")
        )
        
        return parsed_data
    
    def _parse_transfer_webhook(self, payload: dict) -> TransferWebhookData:
        """Parse transfer-specific webhook data."""
        event = str(payload.get("event", ""))
        data = payload.get("data", {})
        
        transfer_status = self._determine_transfer_status(event, str(data.get("status", "")))
        
        parsed_data = TransferWebhookData(
            event_type="transfer",
            status=str(transfer_status.value if hasattr(transfer_status, "value") else transfer_status),
            reference=data.get("reference", ""),
            provider_reference=str(data.get("id", "")),
            amount=Decimal(str(data.get("amount", 0))) / 100,
            currency=data.get("currency", ""),
            raw_data=payload
        )
        return parsed_data
    
    def _determine_payment_status(self, event: str, transaction_status: str) -> PaymentStatus:
        """Determine payment status from event and transaction status."""
        status_mapping = {
            "success": PaymentStatus.COMPLETED,
            "failed": PaymentStatus.FAILED,
            "abandoned": PaymentStatus.ABANDONED,
            "reversed": PaymentStatus.REVERSED,
            "pending": PaymentStatus.PENDING
        }
        return status_mapping.get(transaction_status, PaymentStatus.PENDING)
    
    def _determine_transfer_status(self, event: str, status: str) -> TransferStatus:
        """Determine transfer status from event and status."""
        status_mapping = {
            "success": TransferStatus.COMPLETED,
            "failed": TransferStatus.FAILED,
            "pending": TransferStatus.PENDING,
            "reversed": TransferStatus.REVERSED
        }
        return status_mapping.get(status, TransferStatus.PENDING)