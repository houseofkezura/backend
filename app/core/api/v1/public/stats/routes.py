from __future__ import annotations

from flask_jwt_extended import jwt_required
from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
from .controllers import StatsController
from . import bp


@bp.get("")
@jwt_required()
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Statistics"],
    summary="Get User Statistics",
    description="Get comprehensive statistics about the authenticated user's activity including eSIM purchases, orders, and payments"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse))
def get_stats():
    """Get comprehensive statistics for the current user."""
    return StatsController.get_stats()

