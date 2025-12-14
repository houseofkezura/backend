"""
Admin loyalty routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response_data import (
    LoyaltyAccountListData,
    LoyaltyAdjustData,
    ValidationErrorData,
)
from app.schemas.admin import LoyaltyAdjustRequest
from app.utils.decorators.auth import roles_required
from .controllers import AdminLoyaltyController
from . import bp


@bp.get("/accounts")
@roles_required("Super Admin", "Admin", "Operations", "Finance")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Loyalty"],
    summary="List Loyalty Accounts",
    description="List all loyalty accounts. Requires admin role.",
    responses={
        "200": LoyaltyAccountListData,
        "401": None,
        "403": None,
        "500": None,
    },
)
def list_accounts():
    """List all loyalty accounts."""
    return AdminLoyaltyController.list_accounts()


@bp.post("/accounts/<account_id>/adjust")
@roles_required("Super Admin", "Admin", "Finance")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=LoyaltyAdjustRequest,
    tags=["Admin - Loyalty"],
    summary="Adjust Points",
    description="Manually adjust points for a loyalty account. Requires admin role.",
    responses={
        "200": LoyaltyAdjustData,
        "400": ValidationErrorData,
        "401": None,
        "403": None,
        "404": None,
        "500": None,
    },
)
def adjust_points(account_id: str):
    """Adjust points for a loyalty account."""
    return AdminLoyaltyController.adjust_points(account_id)

