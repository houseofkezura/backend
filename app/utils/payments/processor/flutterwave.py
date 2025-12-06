import requests, hmac, hashlib
from flask import request, json
from decimal import Decimal
from typing import Any, Optional

from app.utils.payments.processor import PaymentVerificationResponse

from ....logging import log_event, log_error
from . import PaymentProcessor, PaymentProcessorResponse
from ..exceptions import SignatureError
from ..types import PaymentProcessorResponse, PaymentWebhookData, TransferWebhookData
from ....enums import TransferStatus, PaymentStatus

class FlutterwaveProcessor(PaymentProcessor):
    """
    Handles payments via Flutterwave API.
    """
    reference_prefix = "flw_"
    supported_currencies = {"NGN", "USD", "GHS", "KES", "ZAR", "EUR", "GBP"}
    
    def initialize_payment(self, amount: float | Decimal, currency: str, customer_data: dict, redirect_url: Optional[str] = None) -> PaymentProcessorResponse:
        """
        Initialize payment with Flutterwave.
        
        Args:
            amount (float | Decimal): Payment amount
            currency (str): Payment currency code
            customer_data (dict): Customer information (email, name)
            
        Returns:
            PaymentProcessorResponse: Standardized payment response
        """
        url = "https://api.flutterwave.com/v3/payments"
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        # Convert to Decimal first for validation
        amount_decimal = Decimal(str(amount)) if isinstance(amount, float) else amount
        
        log_event("redirect_url", redirect_url)
        
        data = {
            "tx_ref": self.reference,
            "amount": str(amount_decimal),
            "currency": currency,
            "redirect_url": redirect_url,
            "customer": {
                "email": customer_data["email"],
                "name": customer_data["name"]
            }
        }

        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()
        data = response_data.get("data", {})
        
        log_event("flw init response_data", response_data)
        
        payment_response = PaymentProcessorResponse(
            status = "success" if response_data["status"] == "success" else "error",
            message = response_data.get("message", ""),
            payment_id = data.get("reference") if data else "",
            authorization_url = data.get("link") if data else "",
            reference = self.reference,
        )
        return payment_response

    def verify_payment(self, payment_reference: str) -> PaymentVerificationResponse:
        """Verify Flutterwave payment status."""
        url = f"https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={payment_reference}"
        
        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers)
        response_data = response.json()
        data = response_data.get("data", {})
        
        log_event("---Flutterwave Response Data for Payment Verification---", response_data)
        
        status_mapping = {
            "successful": PaymentStatus.COMPLETED,
            "failed": PaymentStatus.FAILED,
            "pending": PaymentStatus.PENDING
        }
        
        verification_response = PaymentVerificationResponse(
            status=status_mapping.get(data.get("status", ""), PaymentStatus.PENDING),
            amount=Decimal(str(data.get("amount", 0))),
            currency=data.get("currency", ""),
            provider_reference=data.get("flw_ref", ""),
            meta_info=data.get("meta", {}),
            raw_data=response_data
        )
        
        return verification_response

    def verify_webhook_signature(self, payload: dict = None, signature: str | None = None) -> bool:
        """
        Verify Flutterwave webhook signature.
        
        Args:
            payload: Webhook request body (unused, kept for interface consistency)
            signature: Signature from webhook header (unused, extracted from request)
            
        Returns:
            bool: True if signature is valid
            
        Raises:
            SignatureError: If signature is missing or invalid
        """
        signature = request.headers.get('verif-hash') # get signature
        secret_hash = self.secret_hash # Get secret hash from settings
        
        if not signature:
            raise SignatureError("Missing Flutterwave verification hash")
        
        if signature != secret_hash:
            # This request isn"t from Flutterwave; discard
            raise SignatureError("Invalid Flutterwave signature")
        
        return True
    
    
    def parse_webhook_event(self, payload: dict) -> PaymentWebhookData | TransferWebhookData:
        """
        Parse Flutterwave webhook payload into standard format based on event type.
        
        Args:
            payload: Raw webhook payload
            
        Returns:
            PaymentWebhookData or TransferWebhookData based on event type
        """
        
        event = payload.get("event", "")
        
        event_mapping = {
            "charge": self._parse_payment_webhook,
            "transfer": self._parse_transfer_webhook,
            "": self._parse_payment_webhook
        }
        
        for key, handler in event_mapping.items():
            if event.startswith(key):
                return handler(payload)
        
        raise ValueError(f"Unsupported webhook event: {event}")
    
    def _parse_payment_webhook(self, payload: dict) -> PaymentWebhookData:
        event = payload.get("event") # event key only available in v3
        data = payload.get("data", {}) if event else payload # fallback to payload if flutterwave uses v2 webhook
        transaction_status = data.get("status", "").lower()
        
        payment_status = self._determine_payment_status(event, transaction_status)
        
        parsed_data = PaymentWebhookData(
            event_type="payment",
            status=payment_status,
            reference=data.get("tx_ref", data.get("txRef", "")),
            provider_reference=str(data.get("id", "")),
            amount=Decimal(str(data.get("amount", 0))),
            currency=data.get("currency", ""),
            raw_data=data,
            gateway_response=data.get("processor_response"),
            customer_code=data.get("customer", {}).get("customer_code")
        )
        
        return parsed_data
    
    def _parse_transfer_webhook(self, payload: dict) -> TransferWebhookData:
        """Parse transfer-specific webhook data."""
        event = payload.get("event")
        data = payload.get("data", {})
        transaction_status = data.get("status", "").lower()
        
        transfer_status = self._determine_transfer_status(event, transaction_status)
        
        parsed_data = TransferWebhookData(
            event_type="transfer",
            status=transfer_status,
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
            "successful": PaymentStatus.COMPLETED,
            "failed": PaymentStatus.FAILED,
            "pending": PaymentStatus.PENDING,
            "abandoned": PaymentStatus.ABANDONED,
            "reversed": PaymentStatus.REVERSED,
            "cancelled": PaymentStatus.CANCELLED,
        }
        return status_mapping.get(transaction_status, PaymentStatus.PENDING)
    
    def _determine_transfer_status(self, event: str, status: str) -> TransferStatus:
        """Determine transfer status from event and status."""
        status_mapping = {
            "successful": TransferStatus.COMPLETED,
            "failed": TransferStatus.FAILED,
            "pending": TransferStatus.PENDING,
            "reversed": TransferStatus.REVERSED
        }
        return status_mapping.get(status, TransferStatus.PENDING)



