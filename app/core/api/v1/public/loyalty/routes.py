"""
Public loyalty routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
from app.utils.decorators.auth import customer_required
from .controllers import LoyaltyController
from . import bp


@bp.get("/me")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Loyalty"],
    summary="Get Loyalty Information",
    description="Get current user's loyalty tier, points balance, and progress to next tier"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse, HTTP_500=ErrorResponse))
def get_loyalty_info():
    """Get loyalty account information."""
    return LoyaltyController.get_loyalty_info()


@bp.get("/ledger")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Loyalty"],
    summary="Get Loyalty Ledger",
    description="Get loyalty points transaction history with filtering and pagination"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse, HTTP_500=ErrorResponse))
def get_ledger():
    """Get loyalty ledger entries."""
    return LoyaltyController.get_ledger()

