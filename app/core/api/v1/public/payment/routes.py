from __future__ import annotations

from flask import request
from flask_jwt_extended import jwt_required
from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme, QueryParameter
from app.schemas.response import SuccessResponse, ErrorResponse
from app.schemas.payments import CheckoutRequest, VerifyPaymentRequest, InitPaymentRequest
from .controllers import PaymentController
from . import bp


@bp.post("/initialize")
@jwt_required()
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=InitPaymentRequest,
    tags=["Payments"],
    summary="Initialize Payment",
    description="Initialize payment for a product, service or order using a payment gateway"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse))
def initialize_payment():
    """Initialize payment."""
    return PaymentController.initialize_payment()

@bp.post("/verify")
@jwt_required()
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=VerifyPaymentRequest,
    tags=["Payments"],
    summary="Verify Payment",
    description="Verify payment for a product, service or order"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse))
def verify_payment():
    """Verify payment."""
    return PaymentController.verify()

@bp.post("/checkout")
@jwt_required()
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=CheckoutRequest,
    tags=["Payments"],
    summary="Create Payment Session",
    description="Initialize payment for an order or offer"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse))
def checkout():
    """Create a payment session."""
    return PaymentController.checkout()


@bp.post("/webhook")
@endpoint(
    tags=["Payments"],
    summary="Payment Webhook",
    description="Handle payment webhook from payment provider (Flutterwave/Stripe)"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse))
def webhook():
    """Handle payment webhook."""
    return PaymentController.webhook()


@bp.get("/status/<tx_id>")
@jwt_required()
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Payments"],
    summary="Get Payment Status",
    description="Check the status of a payment transaction"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_404=ErrorResponse, HTTP_401=ErrorResponse))
def get_payment_status(tx_id: str):
    """Get payment status by transaction ID."""
    return PaymentController.get_payment_status(tx_id)


@bp.get("/history")
@jwt_required()
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Payments"],
    summary="Get Payment History",
    description="Get paginated payment history for the authenticated user with optional status filtering",
    query_params=[
        QueryParameter("page", "integer", required=False, description="Page number for pagination", default=1),
        QueryParameter("per_page", "integer", required=False, description="Number of items per page", default=20),
        QueryParameter("status", "string", required=False, description="Filter by payment status (pending, processing, completed, failed, cancelled, refunded, reversed, expired, abandoned)", default=None),
    ]
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse))
def get_payment_history():
    """Get payment history for the current user."""
    return PaymentController.get_payment_history()


