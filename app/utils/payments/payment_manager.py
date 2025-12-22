from typing import Optional, cast
from decimal import Decimal
from flask import url_for
import uuid

from ...extensions import db
from ...logging import log_event, log_error
from .exceptions import TransactionMissingError
from .types import (
    PaymentWebhookData,
    TransferWebhookData,
    PaymentProcessorResponse,
    PaymentVerificationResponse,
)
from .utils import record_payment_transaction, safe_compare_amounts
from .wallet import credit_wallet
from .processor import PaymentProcessor
from .processor.bitpay import BitPayProcessor
from .processor.flutterwave import FlutterwaveProcessor
from .processor.paystack import PaystackProcessor
from ..helpers.money import quantize_amount
from quas_utils.api import success_response, error_response
from ..app_settings.utils import get_active_payment_gateway, get_general_setting
from ..helpers.site import get_site_url, get_platform_url
from quas_utils.decorators import retry
from ...enums import PaymentGatewayName, PaymentStatus, PaymentType
from ...models import AppUser, Payment, Transaction, Subscription
from quas_utils.misc import generate_random_string


class PaymentManager:
    def __init__(self):
        self.processors = {
            "bitpay": BitPayProcessor,
            "flutterwave": FlutterwaveProcessor,
            "paystack": PaystackProcessor
        }
        self.payment_gateway = get_active_payment_gateway()


    def get_payment_processor(self) -> Optional[BitPayProcessor | FlutterwaveProcessor | PaystackProcessor]:
        """
        Returns an instance of the correct payment processor based on the configured provider.
        
        Returns:
            Optional[BitPayProcessor | FlutterwaveProcessor | PaystackProcessor]: Instance of a payment processor.
        """
        
        payment_gateway = self.payment_gateway

        if not isinstance(payment_gateway, dict) or not payment_gateway.get("credentials"):
            raise ValueError("Payment gateway not properly configured")
        
        provider = str(payment_gateway.get("provider", "")).lower()
        credentials = payment_gateway.get("credentials", {})
        
        # Convert test_mode to boolean
        test_mode = credentials.get("test_mode", "false").lower() == "true"  # Converts to True/False
        
        # Get keys safely
        api_key = credentials.get("test_api_key" if test_mode else "api_key", "")
        secret_key = credentials.get("test_secret_key" if test_mode else "secret_key", "")
        public_key = credentials.get("test_public_key" if test_mode else "public_key", "")
        
        processors:dict[str, BitPayProcessor | FlutterwaveProcessor | PaystackProcessor] = {
            "bitpay": BitPayProcessor(
                secret_key=secret_key,
                public_key=public_key,
                api_key=api_key
            ),
            "flutterwave": FlutterwaveProcessor(
                secret_key=secret_key,
                public_key=public_key,
                api_key=api_key
            ),
            "paystack": PaystackProcessor(
                secret_key=secret_key,
                public_key=public_key,
                api_key=api_key
            )
        }
        
        return processors.get(provider)


    def initialize_gateway_payment(
        self,
        amount: Decimal,
        currency: str,
        user: Optional[AppUser],
        payment_type: PaymentType = PaymentType.WALLET_TOP_UP,
        narration: Optional[str] = None,
        extra_meta: Optional[dict] = None,
        redirect_url: Optional[str] = None) -> PaymentProcessorResponse:
        """
        Initialize payment with any gateway and return standardized response.
        
        Args:
            amount: Payment amount
            currency: Payment currency
            user: AppUser
            payment_type: Type of payment (wallet, order, subscription)
            narration: Payment Narration
            extra_meta: Additional metadata (e.g., order_id, subscription_id)
            redirect_url: URL where users should be redirected to
        
        Returns:
            PaymentProcessorResponse: Standardized payment response
        """
        try:
            processor = self.get_payment_processor()
            if processor is None:
                raise ValueError("No active payment processor configured")
            
            if payment_type == PaymentType.WALLET_TOP_UP and user is None:
                raise ValueError("User is required for wallet top-up payments")
            
            amount = quantize_amount(amount)
            
            extra_meta = extra_meta or {}
            
            # Create payment and transaction records using processor's reference
            payment, transaction = record_payment_transaction(
                user=user,
                amount=amount,
                payment_method=processor.__class__.__name__.replace('Processor', '').lower(),
                status=PaymentStatus.PENDING,
                narration=narration or "",
                reference=processor.reference,  # Using the processor's reference
                payment_type=payment_type,
                currency=currency,
                extra_meta=extra_meta
            )
        
            # Use the passed `redirect_url`, or fall back to default
            if not redirect_url:
                if payment_type == PaymentType.WALLET_TOP_UP:
                    redirect_url = f"{get_platform_url()}/payments/verify/?payment_type={str(PaymentType.WALLET_TOP_UP)}"
                elif payment_type == PaymentType.ORDER_PAYMENT:
                    redirect_url = f"{get_platform_url()}/payments/verify/?payment_type={str(PaymentType.ORDER_PAYMENT)}"
                else:
                    redirect_url = f"{get_platform_url()}/payments/verify"
            
            log_event("redirect_url", redirect_url)
            
            customer_email = None
            customer_name = None
            customer_phone = None
            if user:
                customer_email = user.email
                customer_name = user.full_name
                try:
                    customer_phone = user.profile.phone if user.profile else None
                except Exception:
                    customer_phone = None
            else:
                customer_email = extra_meta.get("guest_email")
                customer_name = extra_meta.get("guest_name")
                customer_phone = extra_meta.get("guest_phone")
            
            customer_data = {
                "email": customer_email,
                "name": customer_name,
                "phone": customer_phone,
            }
            # user system currency
            platform_currency = currency or get_general_setting('CURRENCY', default='NGN')
            
            # Initialize payment with gateway
            response = processor.initialize_payment(amount, platform_currency, customer_data, redirect_url)
            
            return response

        except Exception as e:
            # Log the error with original response
            ref = processor.reference if 'processor' in locals() and processor else generate_random_string(12)
            log_error("payment_init_failed", str(e), exc_info=e)
            
            # Return standardized error response
            return PaymentProcessorResponse(
                status="error",
                message="An unexpected error occurred initializing payment",
                payment_id=None,
                authorization_url=None,
                reference=ref  # Using reference if available
            )


    def verify_gateway_payment(self, payment: Payment) -> PaymentVerificationResponse:
        """
        Verify payment status with gateway and handle response.
        
        Args:
            processor: Payment processor instance
            payment: Payment record to verify
        
        Returns:
            PaymentVerificationResponse: Standardized verification response
        """
        try:
            processor = self.get_payment_processor()
            if processor is None:
                raise ValueError("No active payment processor configured")

            verification_response = processor.verify_payment(payment.key)
            
            # Validate amount matches
            response_amount = Decimal(verification_response["amount"])
            payment_amount = Decimal(payment.amount)
            if response_amount != payment_amount:
                raise ValueError("Verified amount doesn't match payment record")
            
            return cast(PaymentVerificationResponse, verification_response)
        except Exception as e:
            log_error("payment_verification_failed", str(e), exc_info=e)
            # Fallback structure adhering to PaymentVerificationResponse
            return PaymentVerificationResponse(
                status=PaymentStatus.FAILED,
                amount=payment.amount,
                currency=payment.currency_code,
                provider_reference=payment.key,
                meta_info={"error": str(e)},
                raw_data={},
            )

    def handle_gateway_payment(self, payment: Payment, verification_response: PaymentVerificationResponse):
        # Handle payment completion based on payment type
        if verification_response['status'] == PaymentStatus.COMPLETED:
            self.handle_completed_payment(payment, verification_response)
        elif verification_response['status'] == PaymentStatus.ABANDONED:
            self.handle_abandoned_payment(payment)
        elif verification_response["status"] == PaymentStatus.FAILED:
            self.handle_failed_payment(payment)
        else:
            self.handle_failed_payment(payment)
            
            
        db.session.commit()

    def handle_gateway_webhook(self, webhook_data: PaymentWebhookData | TransferWebhookData):
        event_type = webhook_data.get('event_type')
        
        log_event("event_type", event_type)
    
        if event_type == 'payment':
            return self._handle_payment_webhook(cast(PaymentWebhookData, webhook_data))
        elif event_type == 'transfer':
            return self._handle_transfer_webhook(cast(TransferWebhookData, webhook_data))
        else:
            raise ValueError(f"Unknown event type: {event_type}")
    
    def _handle_payment_webhook(self, webhook_data: PaymentWebhookData):
        """
        Handle payment webhook events.
        
        Args:
            webhook_data: Standardized payment webhook data
            
        Returns:
            Flask Response object
            
        Raises:
            TransactionMissingError: If payment record not found
            ValueError: If payment amount mismatch
        """
        
        # Find related order
        # Find payment record
        payment: Payment = Payment.query.filter_by(key=webhook_data["reference"]).first()
        if not payment:
            raise TransactionMissingError(f"Payment not found: {webhook_data['reference']}")
        
        log_event("payment", payment)
        
        # Validate amount matches
        webhook_amount = Decimal(webhook_data["amount"])
        payment_amount = Decimal(payment.amount)
        if not safe_compare_amounts(webhook_amount, payment_amount):
            raise ValueError("Verified amount doesn't match payment record")
            
        
        if webhook_data["status"] == PaymentStatus.COMPLETED:
            # Handle successful payment (top-up wallet, update order, etc.)
            self.handle_completed_payment(payment)
        elif webhook_data["status"] == PaymentStatus.ABANDONED:
            self.handle_abandoned_payment(payment)
        elif webhook_data["status"] == PaymentStatus.FAILED:
            self.handle_failed_payment(payment)
        
        db.session.commit()
        
        return success_response("Payment webhook processed successfully", 200)
    
    def _handle_transfer_webhook(self, webhook_data: TransferWebhookData):
        """
        Handle transfer webhook events.
        
        Args:
            webhook_data: Standardized transfer webhook data
            
        Returns:
            Flask Response object
            
        Raises:
            TransactionMissingError: If transfer record not found
            ValueError: If transfer amount mismatch
        """
        
        # TODO: Finish up function to handle transfer webhook
    
        # # Find transfer record
        # transfer = Transfer.query.filter_by(reference=webhook_data["reference"]).first()
        # if not transfer:
        #     raise TransactionMissingError(f"Transfer not found: {webhook_data['reference']}")
        
        # # Validate amount matches
        # if webhook_data["status"] == TransferStatus.COMPLETED:
        #     if webhook_data["amount"] != transfer.amount:
        #         raise ValueError("Transfer amount mismatch")
                
        #     # Handle successful transfer (update recipient balance, etc.)
        #     handle_transfer_completion(transfer)
        
        # # Update transfer status
        # transfer.update(
        #     status=webhook_data["status"],
        #     provider_reference=webhook_data["provider_reference"]
        # )
        
        # return success_response("Transfer webhook processed successfully", 200)


    def handle_completed_payment(self, payment: Payment, verification: Optional[PaymentVerificationResponse] = None) -> None:
        """
        Handle different types of successful payments.
        
        Args:
            payment: Verified payment record
            verification: Payment verification response
        """
        try:
            payment_type = payment.meta_info.get('payment_type', str(PaymentType.WALLET_TOP_UP))
            
            log_event("payment_type", payment_type)
            
            transaction: Transaction = Transaction.query.filter_by(key=payment.key).first()
            
            if payment.status != str(PaymentStatus.COMPLETED):
                if payment_type == str(PaymentType.WALLET_TOP_UP):
                    if payment.app_user:
                    user: AppUser = payment.app_user
                    credit_wallet(user.id, payment.amount, commit=False)
                
                elif payment_type == str(PaymentType.ORDER_PAYMENT):
                    # Handle order payment - update order status and inventory
                    order_id = payment.meta_info.get('order_id')
                    guest_token = payment.meta_info.get('guest_token')
                    
                    if order_id:
                        from ...models.order import Order
                        from ...models.cart import Cart
                        from ...enums.orders import OrderStatus
                        
                        try:
                            order_uuid = uuid.UUID(order_id)
                            order: Optional[Order] = Order.query.filter_by(id=order_uuid).first()
                            
                            if order:
                                order.update(status=str(OrderStatus.PAID), payment_ref=payment.key, commit=False)
                                # Decrement inventory for order items
                                for item in order.items:
                                    variant = item.variant
                                    if variant and variant.inventory:
                                        variant.inventory.quantity = max(0, variant.inventory.quantity - item.quantity)
                                # Clear cart for this user/guest to avoid stale items
                                cart = None
                                if order.user_id:
                                    cart = Cart.query.filter_by(user_id=order.user_id).first()
                                elif guest_token:
                                    cart = Cart.query.filter_by(guest_token=guest_token).first()
                                if cart:
                                    for cart_item in list(cart.items):
                                        db.session.delete(cart_item)
                                log_event("order_payment_completed", f"Order payment completed for order_id={order_id}")
                            else:
                                log_error("Order not found", {"order_id": order_id})
                        except ValueError:
                            log_error("Invalid order_id format", order_id)
                
                elif payment_type == str(PaymentType.SUBSCRIPTION):
                    subscription_id = payment.meta_info.get('subscription_id')
                    if subscription_id:
                        subscription: Subscription = Subscription.query.get(subscription_id)
                        subscription.extend_validity()
                
                # Update payment status
                payment.update(status=str(PaymentStatus.COMPLETED), commit=False)
                if transaction:
                    transaction.update(status=str(PaymentStatus.COMPLETED), commit=False)
        except Exception as e:
            log_error("payment_completion_failed", str(e), exc_info=e)
            raise e

    def handle_abandoned_payment(self, payment: Payment) -> None:
        try:
            transaction: Transaction = Transaction.query.filter_by(key=payment.key).first()
            if payment.status != str(PaymentStatus.ABANDONED):
                payment.update(status=str(PaymentStatus.ABANDONED), commit=False)
                transaction.update(status=str(PaymentStatus.ABANDONED), commit=False)
        except Exception as e:
            log_error("payment_abandoned_failed", str(e), exc_info=e)
            raise e
    
    def handle_failed_payment(self, payment: Payment) -> None:
        try:
            transaction: Transaction = Transaction.query.filter_by(key=payment.key).first()
            if payment.status != str(PaymentStatus.FAILED):
                payment.update(status=str(PaymentStatus.FAILED), commit=False)
                transaction.update(status=str(PaymentStatus.FAILED), commit=False)
        except Exception as e:
            log_error("payment_failed_handling", str(e), exc_info=e)
            raise e

