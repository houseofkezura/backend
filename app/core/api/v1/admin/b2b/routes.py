"""
Admin B2B routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response_data import (
    B2BInquiryListData,
    B2BInquiryStatusData,
    ValidationErrorData,
)
from app.schemas.admin import B2BUpdateStatusRequest
from app.utils.decorators.auth import roles_required
from .controllers import AdminB2BController
from . import bp


@bp.get("/inquiries")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - B2B"],
    summary="List B2B Inquiries",
    description="List all B2B inquiries. Requires admin role.",
    responses={
        "200": B2BInquiryListData,
        "401": None,
        "403": None,
        "500": None,
    },
)
def list_inquiries():
    """List all B2B inquiries."""
    return AdminB2BController.list_inquiries()


@bp.patch("/inquiries/<inquiry_id>/status")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=B2BUpdateStatusRequest,
    tags=["Admin - B2B"],
    summary="Update B2B Inquiry Status",
    description="Update B2B inquiry status. Requires admin role.",
    responses={
        "200": B2BInquiryStatusData,
        "400": ValidationErrorData,
        "401": None,
        "403": None,
        "404": None,
        "500": None,
    },
)
def update_inquiry_status(inquiry_id: str):
    """Update B2B inquiry status."""
    return AdminB2BController.update_inquiry_status(inquiry_id)

