"""
Admin loyalty routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response import (
    SuccessResp,
    BadRequestResp,
    UnauthorizedResp,
    ForbiddenResp,
    NotFoundResp,
    ServerErrorResp,
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
        "200": SuccessResp,
        "401": UnauthorizedResp,
        "403": ForbiddenResp,
        "500": ServerErrorResp,
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
        "200": SuccessResp,
        "400": BadRequestResp,
        "401": UnauthorizedResp,
        "403": ForbiddenResp,
        "404": NotFoundResp,
        "500": ServerErrorResp,
    },
)
def adjust_points(account_id: str):
    """Adjust points for a loyalty account."""
    return AdminLoyaltyController.adjust_points(account_id)

