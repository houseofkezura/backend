"""
Public revamp request routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
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
    description="Create a new revamp request for a wig from a previous order"
)
@spec.validate(resp=Response(HTTP_201=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def create_revamp_request():
    """Create a revamp request."""
    return RevampController.create_revamp_request()


@bp.get("/<revamp_id>/status")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Revamps"],
    summary="Get Revamp Request Status",
    description="Get the status of a revamp request"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def get_revamp_status(revamp_id: str):
    """Get revamp request status."""
    return RevampController.get_revamp_status(revamp_id)

