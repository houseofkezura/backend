"""
Public cart routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint
from app.schemas.response import (
    SuccessResp,
    BadRequestResp,
    UnauthorizedResp,
    ForbiddenResp,
    NotFoundResp,
    ServerErrorResp,
)
from app.schemas.cart import AddCartItemRequest, UpdateCartItemRequest, ApplyPointsRequest
from .controllers import CartController
from . import bp


@bp.get("")
@endpoint(
    tags=["Cart"],
    summary="Get Cart",
    description="Get the current user's cart or guest cart. No authentication required for guests.",
    responses={
        "200": SuccessResp,
        "500": ServerErrorResp,
    },
)
def get_cart():
    """Get cart contents."""
    return CartController.get_cart()


@bp.post("/items")
@endpoint(
    request_body=AddCartItemRequest,
    tags=["Cart"],
    summary="Add Item to Cart",
    description="Add a product variant to the cart. No authentication required for guests.",
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "404": NotFoundResp,
        "500": ServerErrorResp,
    },
)
def add_item():
    """Add item to cart."""
    return CartController.add_item()


@bp.put("/items/<item_id>")
@endpoint(
    request_body=UpdateCartItemRequest,
    tags=["Cart"],
    summary="Update Cart Item",
    description="Update the quantity of a cart item. No authentication required for guests.",
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "403": ForbiddenResp,
        "404": NotFoundResp,
        "500": ServerErrorResp,
    },
)
def update_item(item_id: str):
    """Update cart item quantity."""
    return CartController.update_item(item_id)


@bp.delete("/items/<item_id>")
@endpoint(
    tags=["Cart"],
    summary="Remove Cart Item",
    description="Remove an item from the cart. No authentication required for guests.",
    responses={
        "200": SuccessResp,
        "403": ForbiddenResp,
        "404": NotFoundResp,
        "500": ServerErrorResp,
    },
)
def delete_item(item_id: str):
    """Remove item from cart."""
    return CartController.delete_item(item_id)


@bp.post("/apply-points")
@endpoint(
    request_body=ApplyPointsRequest,
    tags=["Cart"],
    summary="Apply Loyalty Points",
    description="Calculate discount from loyalty points. Requires authentication.",
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "401": UnauthorizedResp,
        "404": NotFoundResp,
        "500": ServerErrorResp,
    },
)
def apply_points():
    """Apply loyalty points to cart."""
    return CartController.apply_points()




