"""
Public checkout routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint
from app.schemas.response import SuccessResponse, ErrorResponse
from app.schemas.checkout import CheckoutRequest
from .controllers import CheckoutController
from . import bp


@bp.post("")
@endpoint(
    request_body=CheckoutRequest,
    tags=["Checkout"],
    summary="Process Checkout",
    description="Process checkout and create order. Supports both authenticated users and guest checkout. Guest orders between ₦200k-₦500k automatically create accounts."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_500=ErrorResponse))
def create_checkout():
    """Process checkout."""
    return CheckoutController.create_checkout()

