"""
Public shipping routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, QueryParameter
from app.schemas.response_data import ShippingZonesData
from .controllers import ShippingController
from . import bp


@bp.get("/zones")
@endpoint(
    tags=["Shipping"],
    summary="Get Shipping Zones",
    description="Return shipping methods/costs/ETA per zone for a given country (default NG). Public.",
    query_params=[
        QueryParameter("country", "string", required=False, description="Country code (default: NG)", default="NG"),
    ],
    responses={
        "200": ShippingZonesData,
        "500": None,
    },
)
def get_shipping_zones():
    """Get shipping zones for a country."""
    return ShippingController.get_shipping_zones()




