"""
Public shipping routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, QueryParameter
from app.schemas.response import SuccessResp, ServerErrorResp
from .controllers import ShippingController
from . import bp


@bp.get("/zones")
@endpoint(
    tags=["Shipping"],
    summary="Get Shipping Zones",
    description="Get shipping zones and methods for a country. No authentication required.",
    query_params=[
        QueryParameter("country", "string", required=False, description="Country code (default: NG)", default="NG"),
    ],
    responses={
        "200": SuccessResp,
        "500": ServerErrorResp,
    },
)
def get_shipping_zones():
    """Get shipping zones for a country."""
    return ShippingController.get_shipping_zones()




