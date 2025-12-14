"""
Admin order routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response_data import (
    OrderListData,
    OrderData,
    OrderStatusUpdateData,
    ValidationErrorData,
)
from app.schemas.admin import OrderStatusUpdateRequest
from app.utils.decorators.auth import roles_required
from .controllers import AdminOrderController
from . import bp


@bp.get("")
@roles_required("Super Admin", "Admin", "Operations", "CRM Manager", "Support")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Orders"],
    summary="List Orders",
    description="List all orders with filtering and pagination. Requires admin role.",
    responses={
        "200": OrderListData,
        "401": None,
        "403": None,
        "500": None,
    },
)
def list_orders():
    """List all orders."""
    return AdminOrderController.list_orders()


@bp.get("/<order_id>")
@roles_required("Super Admin", "Admin", "Operations", "CRM Manager", "Support")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Orders"],
    summary="Get Order",
    description="Get a single order by ID. Requires admin role.",
    responses={
        "200": OrderData,
        "400": ValidationErrorData,
        "401": None,
        "403": None,
        "404": None,
        "500": None,
    },
)
def get_order(order_id: str):
    """Get an order by ID."""
    return AdminOrderController.get_order(order_id)


@bp.patch("/<order_id>/status")
@roles_required("Super Admin", "Admin", "Operations", "CRM Manager")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    request_body=OrderStatusUpdateRequest,
    tags=["Admin - Orders"],
    summary="Update Order Status",
    description="Update order status (fulfill, cancel, refund, etc.). Requires admin role.",
    responses={
        "200": OrderStatusUpdateData,
        "400": ValidationErrorData,
        "401": None,
        "403": None,
        "404": None,
        "500": None,
    },
)
def update_order_status(order_id: str):
    """Update order status."""
    return AdminOrderController.update_order_status(order_id)


@bp.post("/<order_id>/cancel")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Orders"],
    summary="Cancel Order",
    description="Cancel an order. Requires admin role.",
    responses={
        "200": OrderData,
        "400": ValidationErrorData,
        "401": None,
        "403": None,
        "404": None,
        "500": None,
    },
)
def cancel_order(order_id: str):
    """Cancel an order."""
    return AdminOrderController.cancel_order(order_id)

