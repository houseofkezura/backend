"""
Public inventory routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint
from app.schemas.response_data import InventoryData
from .controllers import InventoryController
from . import bp


@bp.get("/<sku>")
@endpoint(
    tags=["Inventory"],
    summary="Get Inventory by SKU",
    description="Get inventory information for a product variant by SKU. No authentication required.",
    responses={
        "200": InventoryData,
        "404": None,
        "500": None,
    },
)
def get_inventory_by_sku(sku: str):
    """Get inventory information by SKU."""
    return InventoryController.get_inventory_by_sku(sku)




