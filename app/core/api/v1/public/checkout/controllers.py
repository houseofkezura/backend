"""
Checkout controller for processing orders.
"""

from __future__ import annotations

from flask import Response, request
from typing import Optional
import uuid

from app.extensions import db
from app.models.user import AppUser
from app.schemas.checkout import CheckoutRequest
from app.utils.checkout.service import process_checkout, CheckoutRequest as CheckoutServiceRequest
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class CheckoutController:
    """Controller for checkout endpoints."""

    @staticmethod
    def create_checkout() -> Response:
        """
        Process checkout and create order.
        
        Supports both authenticated users and guest checkout.
        For guest orders between ₦200k-₦500k, automatically creates Clerk account.
        """
        try:
            payload = CheckoutRequest.model_validate(request.get_json())
            current_user = get_current_user()
            
            # Validate guest checkout requirements
            if not current_user:
                if not payload.email:
                    return error_response("Email is required for guest checkout", 400)
                if not payload.phone:
                    return error_response("Phone is required for guest checkout", 400)
            
            # Convert to service request
            service_request = CheckoutServiceRequest(
                cart_id=payload.cart_id,
                guest_token=payload.guest_token,
                shipping_address={
                    "full_name": payload.shipping_address.full_name,
                    "phone": payload.shipping_address.phone,
                    "line1": payload.shipping_address.line1,
                    "line2": payload.shipping_address.line2,
                    "city": payload.shipping_address.city,
                    "state": payload.shipping_address.state,
                    "postal_code": payload.shipping_address.postal_code,
                    "country": payload.shipping_address.country,
                },
                shipping_method=payload.shipping_method,
                payment_method=payload.payment_method,
                payment_token=payload.payment_token,
                apply_points=payload.apply_points,
                points_to_redeem=payload.points_to_redeem,
                idempotency_key=payload.idempotency_key or request.headers.get("Idempotency-Key"),
                email=payload.email,
                phone=payload.phone,
                first_name=payload.first_name,
                last_name=payload.last_name,
            )
            
            # Process checkout
            result = process_checkout(service_request, current_user)
            
            if not result.success:
                return error_response(result.error or "Checkout failed", 400)
            
            response_data = {
                "order_id": result.order_id,
                "payment_status": result.payment_status,
            }
            
            # Include account creation info if applicable
            if result.auto_account_created:
                response_data["account_created"] = True
                response_data["clerk_id"] = result.clerk_id
                response_data["message"] = "Account created automatically. Check your email for login details."
            
            return success_response(
                "Checkout completed successfully",
                200,
                response_data
            )
        except Exception as e:
            log_error("Failed to process checkout", error=e)
            db.session.rollback()
            return error_response("Failed to process checkout", 500)





