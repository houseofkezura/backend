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
    description="Process checkout and create order. Supports both authenticated users and guest checkout. Guest orders between ₦200k-₦500k automatically create accounts.",
    responses={
        "200": CheckoutData,
        "400": ValidationErrorData,
    },
)
def create_checkout():
    """Process checkout."""
    return CheckoutController.create_checkout()




