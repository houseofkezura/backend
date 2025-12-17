from __future__ import annotations

from flask import Response, request
from decimal import Decimal
from typing import Optional
import uuid

from app.extensions import db
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.models.order import Order
from app.models.payment import Payment
from app.schemas.payments import CheckoutRequest, InitPaymentRequest, VerifyPaymentRequest
from app.enums.orders import OrderStatus
from app.enums.payments import PaymentType, PaymentStatus
from app.utils.payments.payment_manager import PaymentManager
from app.utils.payments.exceptions import SignatureError, TransactionMissingError
from app.logging import log_error, log_event
from flask import request


class PaymentController:
    """Controller for payment endpoints."""
    
    @staticmethod
    def initialize_payment() -> Response:
        try:
            current_user = get_current_user()
            payment_manager: PaymentManager = PaymentManager()
            
            # get request data
            payload = InitPaymentRequest.model_validate(request.get_json())
            amount = Decimal(str(payload.get("amount")).replace(",", ""))
            description = payload.get("description", None)
            currency = payload.get("currency", "USD")
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            processor = payment_manager.get_payment_processor() # Get the payment processor for the selected gateway
            
            if not processor:
                return error_response("A payment Gateway has not been setup yet. Please contact admin.", 500)
            
            # Start payment processing
            response = payment_manager.initialize_gateway_payment(
                amount=amount,
                currency=currency,
                user=current_user,
                narration=description
            )
            
            # On successful initialization
            if response["status"] == "success":
                if not response.get("authorization_url", None):
                    return error_response("payment initialization failed", 500, resp_data=response)
                
                return success_response("payment initialized successfully", 200, resp_data=response)
            else:
                return error_response(f"{response.get('message', 'Unknown Payment initialization error')}", 500, resp_data=response)
        except Exception as e:
            log_error("Failed to initialize payment", error=e)
            return error_response("Failed to initialize payment. Please try again.", 500)
    
    @staticmethod
    def verify() -> Response:
        try:
            payment_manager:PaymentManager = PaymentManager()
            
            # get request data
            payload = VerifyPaymentRequest.model_validate(request.get_json())
            reference = payload.reference or None # Extract reference from request body
            
            if not reference:
                return error_response("Payment reference missing", 400)
            
            # Find payment by reference key
            payment: Payment = Payment.query.filter_by(key=reference).first()
            
            if not payment:
                return error_response("Payment record is missing", 404)
            
            # Proceed with verifying the payment using the PaymentManager
            verification_response = payment_manager.verify_gateway_payment(payment)
            
            payment_manager.handle_gateway_payment(payment, verification_response)
            payment_type = payment.meta_info.get("payment_type", str(PaymentType.ORDER_PAYMENT))
            
            if verification_response['status'] != PaymentStatus.COMPLETED:
                return error_response("Payment failed. Please try again.", 400, verification_response)
            
            
            if payment_type == str(PaymentType.WALLET_TOP_UP):
                msg, code, data = "Your wallet has been credited successfully!", 200, None
            
            elif payment_type == str(PaymentType.ORDER_PAYMENT):
                order_id = payment.meta_info.get("order_id")
                msg, code, data = "Your order has been paid for!", 200, {"order_id": order_id}
            elif payment_type == str(PaymentType.SUBSCRIPTION):
                subscription_id = payment.meta_info.get("subscription_id")
                msg, code, data = "Your subscription has been extended successfully!", 200, {"subscription_id": subscription_id}
            else:
                msg, code, data = "Payment verified successfully", 200, None
                
            return success_response(msg, code, data)
        except Exception as e:
            log_error("Failed to verify payment", error=e)
            return error_response("Payment verification failed. Please try again.", 500)

    @staticmethod
    def checkout() -> Response:
        """
        Create a payment session for an order or offer.
        
        If order_id is provided, uses existing order.
        If offer_id is provided, creates new order and eSIM purchase.
        """
        try:
            payload = CheckoutRequest.model_validate(request.get_json())
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            order = None
            
            # Handle existing order
            if not payload.order_id:
                return error_response("order_id must be provided", 400)
            
            try:
                order_uuid = uuid.UUID(payload.order_id)
                order: Order = Order.query.filter_by(id=order_uuid, user_id=current_user.id).first()
            except ValueError:
                return error_response("Invalid order ID format", 400)
            
            if not order:
                return error_response(f"Order '{payload.order_id}' not found", 404)
            
            # Initialize payment
            payment_manager = PaymentManager()
            currency = payload.currency or "USD"
            
            payment_response = payment_manager.initialize_gateway_payment(
                amount=Decimal(str(order.amount)),
                currency=currency,
                user=current_user,
                payment_type=PaymentType.ORDER_PAYMENT,
                narration=f"Payment for order {order.id}",
                extra_meta={
                    "order_id": str(order.id),
                },
                redirect_url=f"{request.host_url}payment/verify"
            )
            
            # Update order with payment reference
            order.payment_ref = payment_response.reference
            db.session.commit()
            
            return success_response(
                "Payment session created successfully",
                200,
                payment_response
            )
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            log_error("Failed to create payment session", error=e)
            db.session.rollback()
            return error_response("Failed to create payment session", 500)

    @staticmethod
    def webhook() -> Response:
        """
        Handle payment webhook from payment provider.
        
        Verifies signature, updates order status, and triggers eSIM activation.
        """
        try:
            payment_manager = PaymentManager()
            payload = request.get_json() # Get webhook data and headers
            
            log_event("Webhook payload", payload)
            
            processor = payment_manager.get_payment_processor()
            
            if not processor:
                return error_response("Payment processor not configured", 500)
            
            # Verify webhook signature
            if not processor.verify_webhook_signature():
                raise SignatureError("Invalid webhook signature")
            
            # Parse webhook data into standard format based on event type
            webhook_data = processor.parse_webhook_event(payload)
            
            # Handle webhook
            api_response = payment_manager.handle_gateway_webhook(webhook_data)
            
            return api_response
        except SignatureError as e:
            log_error("Invalid webhook signature", e)
            return error_response(str(e), e.status_code)
        except TransactionMissingError as e:
            log_error("Transaction not found", e)
            return error_response(str(e), e.status_code)
        except Exception as e:
            log_error("Failed to process payment webhook", error=e)
            return error_response("Failed to process webhook", 500)
        finally:
            db.session.close()

    @staticmethod
    def get_payment_status(tx_id: str) -> Response:
        """
        Get payment status by transaction ID.
        
        Args:
            tx_id: Payment transaction reference
        """
        try:
            current_user = get_current_user()
            guest_email = request.args.get("email")
            
            if not current_user and not guest_email:
                return error_response("Unauthorized", 401)
            
            query = Payment.query.filter_by(key=tx_id)
            if current_user:
                query = query.filter_by(user_id=current_user.id)
            elif guest_email:
                query = query.filter(Payment.meta_info['guest_email'].astext == guest_email)
            
            payment = query.first()
            
            if not payment:
                return error_response(f"Payment '{tx_id}' not found", 404)
            
            return success_response(
                "Payment status retrieved successfully",
                200,
                {
                    "reference": payment.key,
                    "status": payment.status,
                    "amount": float(payment.amount),
                    "currency": payment.currency_code if hasattr(payment, 'currency_code') else "USD",
                    "order_id": payment.meta_info.get('order_id') if payment.meta_info else None,
                    "created_at": payment.created_at.isoformat() if payment.created_at else None,
                    "updated_at": payment.updated_at.isoformat() if payment.updated_at else None,
                }
            )
        except Exception as e:
            log_error(f"Failed to fetch payment status {tx_id}", error=e)
            return error_response("Failed to fetch payment status", 500)
    
    @staticmethod
    def get_payment_history() -> Response:
        """
        Get payment history for the authenticated user.
        
        Returns paginated list of all payments with optional status filtering.
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            # Get pagination parameters
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 20, type=int)
            per_page = max(1, min(per_page, 100))  # Limit between 1 and 100
            
            # Get optional status filter
            status_filter = request.args.get("status", None, type=str)
            
            # Build query
            query = Payment.query.filter_by(user_id=current_user.id).order_by(Payment.created_at.desc())
            
            # Apply status filter if provided
            if status_filter:
                try:
                    # Validate status
                    payment_status = PaymentStatus(status_filter)
                    query = query.filter(Payment.status == str(payment_status))
                except ValueError:
                    return error_response(f"Invalid payment status: {status_filter}", 400)
            
            # Paginate
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            payments: list[Payment] = pagination.items
            
            # Convert to dict
            payment_list = [payment.to_dict() for payment in payments]
            
            response_data = {
                "total": pagination.total,
                "payments": payment_list,
                "current_page": pagination.page,
                "total_pages": pagination.pages,
            }
            
            return success_response(
                "Payment history retrieved successfully",
                200,
                response_data
            )
        except Exception as e:
            log_error("Failed to fetch payment history", error=e)
            return error_response("Failed to fetch payment history", 500)


