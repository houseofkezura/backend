from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response_data import StatsData
from app.utils.decorators.auth import customer_required
from .controllers import StatsController
from . import bp


@bp.get("")
@customer_required
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

