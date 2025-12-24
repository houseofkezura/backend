from __future__ import annotations

from flask import request
from app.extensions.docs import endpoint, SecurityScheme, QueryParameter
from app.schemas.response_data import (
    PaymentInitData,
    PaymentVerificationData,
    PaymentStatusData,
    PaymentHistoryData,
    ValidationErrorData,
)
from app.schemas.payments import PayCheckoutRequest, VerifyPaymentRequest, InitPaymentRequest
from .controllers import PaymentController
from . import bp
from app.utils.decorators.auth import customer_required


@bp.post("/initialize")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=InitPaymentRequest,
    tags=["Payments"],
    summary="Initialize Payment",
    description="Start a standalone payment (e.g., wallet top-up or ad-hoc) using the active payment gateway. Returns authorization_url and reference.",
    responses={
        "200": PaymentInitData,
        "400": ValidationErrorData,
        "401": None,
    },
)
def initialize_payment():
    """Initialize payment."""
    return PaymentController.initialize_payment()

@bp.post("/verify")
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=VerifyPaymentRequest,
    tags=["Payments"],
    summary="Verify Payment",
    description="Verify a payment by reference after returning from the gateway. Also usable as a fallback if webhook is delayed.",
    responses={
        "200": PaymentVerificationData,
        "400": ValidationErrorData,
        "401": None,
    },
)
def verify_payment():
    """Verify payment."""
    return PaymentController.verify()

@bp.post("/checkout")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=PayCheckoutRequest,
    tags=["Payments"],
    summary="Create Payment Session",
    description="Create a payment session for an existing order_id. Returns authorization_url and reference for redirect flows.",
    responses={
        "200": PaymentInitData,
        "400": ValidationErrorData,
        "401": None,
    },
)
def checkout():
    """Create a payment session."""
    return PaymentController.checkout()


@bp.post("/webhook")
@endpoint(
    tags=["Payments"],
    summary="Payment Webhook",
    description="Gateway webhook receiver. Verifies signature, normalizes payload, and finalizes payment/order state.",
    responses={
        "200": None,
        "400": ValidationErrorData,
    },
)
def webhook():
    """Handle payment webhook."""
    return PaymentController.webhook()


@bp.get("/status/<tx_id>")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Payments"],
    summary="Get Payment Status",
    description="Fetch payment status by reference for the current user (or guest via email query).",
    responses={
        "200": PaymentStatusData,
        "401": None,
        "404": None,
    },
)
def get_payment_status(tx_id: str):
    """Get payment status by transaction ID."""
    return PaymentController.get_payment_status(tx_id)


@bp.get("/history")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Payments"],
    summary="Get Payment History",
    description="Paginated payment history for the signed-in user with optional status filter.",
    query_params=[
        QueryParameter("page", "integer", required=False, description="Page number for pagination", default=1),
        QueryParameter("per_page", "integer", required=False, description="Number of items per page", default=20),
        QueryParameter("status", "string", required=False, description="Filter by payment status (pending, processing, completed, failed, cancelled, refunded, reversed, expired, abandoned)", default=None),
    ],
    responses={
        "200": PaymentHistoryData,
        "400": ValidationErrorData,
        "401": None,
    },
)
def get_payment_history():
    """Get payment history for the current user."""
    return PaymentController.get_payment_history()


