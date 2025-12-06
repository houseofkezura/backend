from __future__ import annotations

from flask import request
from flask_jwt_extended import jwt_required
from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, SecurityScheme, QueryParameter
from app.schemas.response import ApiResponse, SuccessResponse, ErrorResponse
from app.schemas.orders import CreateOrderRequest, UpdateOrderStatusRequest, OrderResponse
from .controllers import OrdersController
from . import bp


@bp.post("")
@jwt_required()
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=CreateOrderRequest,
    tags=["Orders"],
    summary="Create Order",
    description="Create a new pending order (before payment)"
)
@spec.validate(resp=Response(HTTP_201=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse))
def create_order():
    """Create a new order."""
    return OrdersController.create_order()


@bp.get("")
@jwt_required()
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Orders"],
    summary="List User Orders",
    description="Get all orders for the authenticated user",
    query_params=[
        QueryParameter("page", "integer", required=False, description="Page number for pagination", default=1),
        QueryParameter("per_page", "integer", required=False, description="Number of items per page", default=8),
    ]
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse))
def list_orders():
    """List all orders for the current user."""
    return OrdersController.list_orders()


@bp.get("/<order_id>")
@jwt_required()
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Orders"],
    summary="Get Order Details",
    description="Get details for a specific order"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_404=ErrorResponse, HTTP_401=ErrorResponse))
def get_order(order_id: str):
    """Get a specific order by ID."""
    return OrdersController.get_order(order_id)


@bp.patch("/<order_id>")
@jwt_required()
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=UpdateOrderStatusRequest,
    tags=["Orders"],
    summary="Update Order Status",
    description="Update the status of an order (admin or system use)"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_404=ErrorResponse, HTTP_401=ErrorResponse))
def update_order_status(order_id: str):
    """Update order status."""
    return OrdersController.update_order_status(order_id)



