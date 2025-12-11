"""
Admin authentication routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response import SuccessResp, UnauthorizedResp, ForbiddenResp
from app.utils.decorators.auth import roles_required
from .controllers import AdminAuthController
from . import bp


@bp.get("/verify")
@roles_required("Super Admin", "Admin", "Operations", "CRM Manager", "Finance", "Support")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Authentication"],
    summary="Verify Admin Authentication",
    description="Verify that the current user has admin privileges",
    responses={
        "200": SuccessResp,
        "401": UnauthorizedResp,
        "403": ForbiddenResp,
    },
)
def verify():
    """Verify admin authentication."""
    return AdminAuthController.verify()