"""
Admin CRM staff routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response_data import (
    StaffListData,
    StaffCreateData,
    ValidationErrorData,
)
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
    description="List all CRM staff. Requires admin role.",
    responses={
        "200": StaffListData,
        "401": None,
        "403": None,
        "500": None,
    },
)
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
    description="Create a new CRM staff member. Requires admin role.",
    responses={
        "201": StaffCreateData,
        "400": ValidationErrorData,
        "401": None,
        "403": None,
        "409": None,
        "500": None,
    },
)
def create_staff():
    """Create a new CRM staff member."""
    return AdminStaffController.create_staff()

