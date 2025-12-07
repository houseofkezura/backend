"""
Admin authentication routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
from app.utils.decorators.auth import roles_required
from .controllers import AdminAuthController
from . import bp


@bp.get("/verify")
@roles_required("Super Admin", "Admin", "Operations", "CRM Manager", "Finance", "Support")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Authentication"],
    summary="Verify Admin Authentication",
    description="Verify that the current user has admin privileges"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse))
def verify():
    """Verify admin authentication."""
    return AdminAuthController.verify()