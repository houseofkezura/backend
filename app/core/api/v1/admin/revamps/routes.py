"""
Admin revamp routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
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
    description="List all revamp requests. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_500=ErrorResponse))
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
    description="Update revamp request status. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def update_request_status(request_id: str):
    """Update revamp request status."""
    return AdminRevampController.update_request_status(request_id)

