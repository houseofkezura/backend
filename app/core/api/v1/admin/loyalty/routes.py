"""
Admin loyalty routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
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
    description="List all loyalty accounts. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_500=ErrorResponse))
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
    description="Manually adjust points for a loyalty account. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def adjust_points(account_id: str):
    """Adjust points for a loyalty account."""
    return AdminLoyaltyController.adjust_points(account_id)

