from __future__ import annotations

from flask_jwt_extended import jwt_required

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response_data import StatsData
from .controllers import StatsController
from . import bp


@bp.get("")
@jwt_required()
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Statistics"],
    summary="Get User Statistics",
    description="Get comprehensive statistics about the authenticated user's activity including eSIM purchases, orders, and payments",
    responses={
        "200": StatsData,
        "401": None,
    },
)
def get_stats():
    """Get comprehensive statistics for the current user."""
    return StatsController.get_stats()

