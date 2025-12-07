from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint, QueryParameter
from app.schemas.response import SuccessResponse, ErrorResponse
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
    ]
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse, HTTP_500=ErrorResponse))
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
    ]
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_404=ErrorResponse, HTTP_401=ErrorResponse, HTTP_500=ErrorResponse))
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
    ]
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def cancel_order(order_id: str):
    """Cancel an order."""
    return OrdersController.cancel_order(order_id)



