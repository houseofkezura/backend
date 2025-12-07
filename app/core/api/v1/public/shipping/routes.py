"""
Public shipping routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, QueryParameter
from app.schemas.response import SuccessResponse, ErrorResponse
from .controllers import ShippingController
from . import bp


@bp.get("/zones")
@endpoint(
    tags=["Shipping"],
    summary="Get Shipping Zones",
    description="Get shipping zones and methods for a country. No authentication required.",
    query_params=[
        QueryParameter("country", "string", required=False, description="Country code (default: NG)", default="NG"),
    ]
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_500=ErrorResponse))
def get_shipping_zones():
    """Get shipping zones for a country."""
    return ShippingController.get_shipping_zones()

