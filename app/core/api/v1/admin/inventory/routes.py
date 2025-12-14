"""
Admin inventory routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response_data import (
    InventoryListData,
    InventoryData,
    InventoryAdjustData,
    ValidationErrorData,
)
from app.schemas.products import InventoryAdjustRequest
from app.utils.decorators.auth import roles_required
from .controllers import AdminInventoryController
from . import bp


@bp.get("")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Inventory"],
    summary="List Inventory",
    description="List all inventory with filtering. Requires admin role.",
    responses={
        "200": InventoryListData,
        "401": None,
        "403": None,
        "500": None,
    },
)
def list_inventory():
    """List all inventory."""
    return AdminInventoryController.list_inventory()


@bp.get("/sku/<sku>")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Inventory"],
    summary="Get Inventory by SKU",
    description="Get inventory information by SKU. Requires admin role.",
    responses={
        "200": InventoryData,
        "401": None,
        "403": None,
        "404": None,
        "500": None,
    },
)
def get_inventory_by_sku(sku: str):
    """Get inventory by SKU."""
    return AdminInventoryController.get_inventory_by_sku(sku)


@bp.post("/adjust")
@roles_required("Super Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=InventoryAdjustRequest,
    tags=["Admin - Inventory"],
    summary="Adjust Inventory",
    description="Adjust inventory quantity for a product variant. Requires admin role.",
    responses={
        "200": InventoryAdjustData,
        "400": ValidationErrorData,
        "401": None,
        "403": None,
        "404": None,
        "500": None,
    },
)
def adjust_inventory():
    """Adjust inventory."""
    return AdminInventoryController.adjust_inventory()

