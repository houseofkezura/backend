from __future__ import annotations

from app.extensions.docs import endpoint, QueryParameter, SecurityScheme
from app.schemas.response_data import (
    OrderListData,
    OrderData,
    ValidationErrorData,
)
from app.utils.decorators.auth import optional_customer_auth
from .controllers import OrdersController
from . import bp


@bp.get("")
@optional_customer_auth
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Orders"],
    summary="List Orders",
    description="Get all orders for authenticated user or guest (requires email query param for guests). Send Authorization header with Clerk token for authenticated access, or email query param for guest orders.",
    query_params=[
        QueryParameter("page", "integer", required=False, description="Page number", default=1),
        QueryParameter("per_page", "integer", required=False, description="Items per page", default=20),
        QueryParameter("email", "string", required=False, description="Email for guest orders (required if no auth token)"),
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
@optional_customer_auth
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Orders"],
    summary="Get Order Details",
    description="Get details for a specific order. Send Authorization header with Clerk token for authenticated access, or email query param for guest orders.",
    query_params=[
        QueryParameter("email", "string", required=False, description="Email for guest orders (required if no auth token)"),
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
@optional_customer_auth
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Orders"],
    summary="Cancel Order",
    description="Cancel an order. Only orders that haven't been shipped can be cancelled. Send Authorization header with Clerk token for authenticated access, or email query param for guest orders.",
    query_params=[
        QueryParameter("email", "string", required=False, description="Email for guest orders (required if no auth token)"),
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



