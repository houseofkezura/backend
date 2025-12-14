"""
Admin revamp routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response_data import (
    RevampRequestListData,
    RevampStatusUpdateData,
    ValidationErrorData,
)
from app.schemas.admin import RevampStatusUpdateRequest
from app.utils.decorators.auth import roles_required
from .controllers import AdminRevampController
from . import bp


@bp.get("")
@roles_required("Super Admin", "Admin", "Operations", "CRM Manager", "CRM Staff")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Revamps"],
    summary="List Revamp Requests",
    description="List all revamp requests. Requires admin role.",
    responses={
        "200": RevampRequestListData,
        "401": None,
        "403": None,
        "500": None,
    },
)
def list_requests():
    """List all revamp requests."""
    return AdminRevampController.list_requests()


@bp.patch("/<request_id>/status")
@roles_required("Super Admin", "Admin", "Operations", "CRM Manager", "CRM Staff")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=RevampStatusUpdateRequest,
    tags=["Admin - Revamps"],
    summary="Update Revamp Request Status",
    description="Update revamp request status. Requires admin role.",
    responses={
        "200": RevampStatusUpdateData,
        "400": ValidationErrorData,
        "401": None,
        "403": None,
        "404": None,
        "500": None,
    },
)
def update_request_status(request_id: str):
    """Update revamp request status."""
    return AdminRevampController.update_request_status(request_id)

