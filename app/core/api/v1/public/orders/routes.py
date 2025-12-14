from __future__ import annotations

from app.extensions.docs import endpoint, QueryParameter
from app.schemas.response_data import (
    OrderListData,
    OrderData,
    ValidationErrorData,
)
from .controllers import OrdersController
from . import bp


@bp.get("")
@endpoint(
    tags=["Orders"],
    summary="List Orders",
    description="Get all orders for authenticated user or guest (requires email query param for guests)",
    query_params=[
        QueryParameter("page", "integer", required=False, description="Page number", default=1),
        QueryParameter("per_page", "integer", required=False, description="Items per page", default=20),
        QueryParameter("email", "string", required=False, description="Email for guest orders"),
    ],
    responses={
        "200": OrderListData,
        "401": None,
        "500": None,
    },
)
def list_orders():
    """List orders for current user or guest."""
    return OrdersController.list_orders()


@bp.get("/<order_id>")
@endpoint(
    tags=["Orders"],
    summary="Get Order Details",
    description="Get details for a specific order. For guests, include email query param.",
    query_params=[
        QueryParameter("email", "string", required=False, description="Email for guest orders"),
    ],
    responses={
        "200": OrderData,
        "401": None,
        "404": None,
        "500": None,
    },
)
def get_order(order_id: str):
    """Get a specific order by ID."""
    return OrdersController.get_order(order_id)


@bp.post("/<order_id>/cancel")
@endpoint(
    tags=["Orders"],
    summary="Cancel Order",
    description="Cancel an order. Only orders that haven't been shipped can be cancelled.",
    query_params=[
        QueryParameter("email", "string", required=False, description="Email for guest orders"),
    ],
    responses={
        "200": OrderData,
        "400": ValidationErrorData,
        "401": None,
        "404": None,
        "500": None,
    },
)
def cancel_order(order_id: str):
    """Cancel an order."""
    return OrdersController.cancel_order(order_id)



