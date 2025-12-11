"""
Public loyalty routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response import SuccessResp, UnauthorizedResp, ServerErrorResp
from app.utils.decorators.auth import customer_required
from .controllers import LoyaltyController
from . import bp


@bp.get("/me")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Loyalty"],
    summary="Get Loyalty Information",
    description="Get current user's loyalty tier, points balance, and progress to next tier",
    responses={
        "200": SuccessResp,
        "401": UnauthorizedResp,
        "500": ServerErrorResp,
    },
)
def get_loyalty_info():
    """Get loyalty account information."""
    return LoyaltyController.get_loyalty_info()


@bp.get("/ledger")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Loyalty"],
    summary="Get Loyalty Ledger",
    description="Get loyalty points transaction history with filtering and pagination",
    responses={
        "200": SuccessResp,
        "401": UnauthorizedResp,
        "500": ServerErrorResp,
    },
)
def get_ledger():
    """Get loyalty ledger entries."""
    return LoyaltyController.get_ledger()




