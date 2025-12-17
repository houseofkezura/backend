"""
Public checkout routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint
from app.schemas.response_data import CheckoutData, ValidationErrorData
from app.schemas.checkout import CheckoutRequest
from .controllers import CheckoutController
from . import bp


@bp.post("/")
@endpoint(
    request_body=CheckoutRequest,
    tags=["Checkout"],
    summary="Process Checkout",
    description="Create an order from cart and start payment. Supports guests (email/phone required) and authenticated users. Returns order_id, payment_reference, and authorization_url for gateway redirect.",
    responses={
        "200": CheckoutData,
        "400": ValidationErrorData,
    },
)
def create_checkout():
    """Process checkout."""
    return CheckoutController.create_checkout()




