"""
Public inventory routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint
from app.schemas.response import SuccessResponse, ErrorResponse
from .controllers import InventoryController
from . import bp


@bp.get("/<sku>")
@endpoint(
    tags=["Inventory"],
    summary="Get Inventory by SKU",
    description="Get inventory information for a product variant by SKU. No authentication required."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def get_inventory_by_sku(sku: str):
    """Get inventory information by SKU."""
    return InventoryController.get_inventory_by_sku(sku)

