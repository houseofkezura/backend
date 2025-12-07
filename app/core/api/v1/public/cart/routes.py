"""
Public cart routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint
from app.schemas.response import SuccessResponse, ErrorResponse
from app.schemas.cart import AddCartItemRequest, UpdateCartItemRequest, ApplyPointsRequest
from .controllers import CartController
from . import bp


@bp.get("")
@endpoint(
    tags=["Cart"],
    summary="Get Cart",
    description="Get the current user's cart or guest cart. No authentication required for guests."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_500=ErrorResponse))
def get_cart():
    """Get cart contents."""
    return CartController.get_cart()


@bp.post("/items")
@endpoint(
    request_body=AddCartItemRequest,
    tags=["Cart"],
    summary="Add Item to Cart",
    description="Add a product variant to the cart. No authentication required for guests."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def add_item():
    """Add item to cart."""
    return CartController.add_item()


@bp.put("/items/<item_id>")
@endpoint(
    request_body=UpdateCartItemRequest,
    tags=["Cart"],
    summary="Update Cart Item",
    description="Update the quantity of a cart item. No authentication required for guests."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def update_item(item_id: str):
    """Update cart item quantity."""
    return CartController.update_item(item_id)


@bp.delete("/items/<item_id>")
@endpoint(
    tags=["Cart"],
    summary="Remove Cart Item",
    description="Remove an item from the cart. No authentication required for guests."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_403=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def delete_item(item_id: str):
    """Remove item from cart."""
    return CartController.delete_item(item_id)


@bp.post("/apply-points")
@endpoint(
    request_body=ApplyPointsRequest,
    tags=["Cart"],
    summary="Apply Loyalty Points",
    description="Calculate discount from loyalty points. Requires authentication."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def apply_points():
    """Apply loyalty points to cart."""
    return CartController.apply_points()

