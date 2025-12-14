"""
Public revamp request routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response_data import (
    RevampRequestData,
    RevampStatusData,
    ValidationErrorData,
)
from app.schemas.revamp import CreateRevampRequest
from app.utils.decorators.auth import customer_required
from .controllers import RevampController
from . import bp


@bp.post("")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=CreateRevampRequest,
    tags=["Revamps"],
    summary="Create Revamp Request",
    description="Create a new revamp request for a wig from a previous order",
    responses={
        "201": RevampRequestData,
        "400": ValidationErrorData,
        "401": None,
        "403": None,
        "404": None,
        "500": None,
    },
)
def create_revamp_request():
    """Create a revamp request."""
    return RevampController.create_revamp_request()


@bp.get("/<revamp_id>/status")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Revamps"],
    summary="Get Revamp Request Status",
    description="Get the status of a revamp request",
    responses={
        "200": RevampStatusData,
        "401": None,
        "404": None,
        "500": None,
    },
)
def get_revamp_status(revamp_id: str):
    """Get revamp request status."""
    return RevampController.get_revamp_status(revamp_id)




