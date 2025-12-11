"""
Admin CRM routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response import SuccessResp, UnauthorizedResp, ForbiddenResp, ServerErrorResp
from app.utils.decorators.auth import roles_required
from .controllers import AdminCrmController
from . import bp


@bp.get("/ratings")
@roles_required("Super Admin", "Admin", "CRM Manager")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - CRM"],
    summary="List CRM Ratings",
    description="List all CRM ratings. Requires admin role.",
    responses={
        "200": SuccessResp,
        "401": UnauthorizedResp,
        "403": ForbiddenResp,
        "500": ServerErrorResp,
    },
)
def list_ratings():
    """List all CRM ratings."""
    return AdminCrmController.list_ratings()




