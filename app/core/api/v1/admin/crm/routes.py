"""
Admin CRM routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
from app.utils.decorators.auth import roles_required
from .controllers import AdminCrmController
from . import bp


@bp.get("/ratings")
@roles_required("Super Admin", "Admin", "CRM Manager")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - CRM"],
    summary="List CRM Ratings",
    description="List all CRM ratings. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_500=ErrorResponse))
def list_ratings():
    """List all CRM ratings."""
    return AdminCrmController.list_ratings()

