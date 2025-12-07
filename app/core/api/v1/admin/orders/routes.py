"""
Admin order routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme
from app.schemas.response import SuccessResponse, ErrorResponse
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
    description="List all orders with filtering and pagination. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_500=ErrorResponse))
def list_orders():
    """List all orders."""
    return AdminOrderController.list_orders()


@bp.get("/<order_id>")
@roles_required("Super Admin", "Admin", "Operations", "CRM Manager", "Support")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Orders"],
    summary="Get Order",
    description="Get a single order by ID. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
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
    description="Update order status (fulfill, cancel, refund, etc.). Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def update_order_status(order_id: str):
    """Update order status."""
    return AdminOrderController.update_order_status(order_id)


@bp.post("/<order_id>/cancel")
@roles_required("Super Admin", "Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Orders"],
    summary="Cancel Order",
    description="Cancel an order. Requires admin role."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def cancel_order(order_id: str):
    """Cancel an order."""
    return AdminOrderController.cancel_order(order_id)

