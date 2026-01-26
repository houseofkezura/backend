"""
Admin waitlist routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response_data import (
    WaitlistListData,
    WaitlistStatusUpdateData,
    WaitlistStatsData,
    ValidationErrorData,
)
from app.schemas.waitlist import UpdateWaitlistStatusRequest
from app.utils.decorators.auth import roles_required
from .controllers import AdminWaitlistController
from . import bp


@bp.get("/entries")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Waitlist"],
    summary="List Waitlist Entries",
    description="List all waitlist entries with pagination and filters. Requires admin role.",
    responses={
        "200": WaitlistListData,
        "401": None,
        "403": None,
        "500": None,
    },
)
def list_entries():
    """List all waitlist entries."""
    return AdminWaitlistController.list_entries()


@bp.patch("/entries/<entry_id>/status")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=UpdateWaitlistStatusRequest,
    tags=["Admin - Waitlist"],
    summary="Update Waitlist Entry Status",
    description="Update waitlist entry status. Requires admin role.",
    responses={
        "200": WaitlistStatusUpdateData,
        "400": ValidationErrorData,
        "401": None,
        "403": None,
        "404": None,
        "500": None,
    },
)
def update_status(entry_id: str):
    """Update waitlist entry status."""
    return AdminWaitlistController.update_status(entry_id)


@bp.delete("/entries/<entry_id>")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Waitlist"],
    summary="Delete Waitlist Entry",
    description="Delete a waitlist entry. Requires admin role.",
    responses={
        "200": None,
        "401": None,
        "403": None,
        "404": None,
        "500": None,
    },
)
def delete_entry(entry_id: str):
    """Delete a waitlist entry."""
    return AdminWaitlistController.delete_entry(entry_id)


@bp.get("/stats")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Waitlist"],
    summary="Get Waitlist Statistics",
    description="Get waitlist statistics (total, pending, invited, converted). Requires admin role.",
    responses={
        "200": WaitlistStatsData,
        "401": None,
        "403": None,
        "500": None,
    },
)
def get_stats():
    """Get waitlist statistics."""
    return AdminWaitlistController.get_stats()
