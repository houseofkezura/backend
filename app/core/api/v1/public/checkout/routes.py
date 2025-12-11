"""
Public checkout routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint
from app.schemas.response import SuccessResp, BadRequestResp, ServerErrorResp
from app.schemas.checkout import CheckoutRequest
from .controllers import CheckoutController
from . import bp


@bp.post("")
@endpoint(
    request_body=CheckoutRequest,
    tags=["Checkout"],
    summary="Process Checkout",
    description="Process checkout and create order. Supports both authenticated users and guest checkout. Guest orders between ₦200k-₦500k automatically create accounts.",
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "500": ServerErrorResp,
    },
)
def create_checkout():
    """Process checkout."""
    return CheckoutController.create_checkout()




