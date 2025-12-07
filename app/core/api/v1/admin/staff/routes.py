"""
Admin CRM staff routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
from app.schemas.admin import StaffCreateRequest
from app.utils.decorators.auth import roles_required
from .controllers import AdminStaffController
from . import bp


@bp.get("")
@roles_required("Super Admin", "Admin", "CRM Manager")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Staff"],
    summary="List CRM Staff",
    description="List all CRM staff. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_500=ErrorResponse))
def list_staff():
    """List all CRM staff."""
    return AdminStaffController.list_staff()


@bp.post("")
@roles_required("Super Admin", "Admin", "CRM Manager")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=StaffCreateRequest,
    tags=["Admin - Staff"],
    summary="Create CRM Staff",
    description="Create a new CRM staff member. Requires admin role."
)
@spec.validate(resp=Response(HTTP_201=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_409=ErrorResponse, HTTP_500=ErrorResponse))
def create_staff():
    """Create a new CRM staff member."""
    return AdminStaffController.create_staff()

