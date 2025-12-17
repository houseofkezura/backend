"""
Public cart routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint
from app.schemas.response_data import (
    CartData,
    CartItemData,
    ValidationErrorData,
)
from app.schemas.cart import AddCartItemRequest, UpdateCartItemRequest, ApplyPointsRequest
from .controllers import CartController
from . import bp


@bp.get("")
@endpoint(
    tags=["Cart"],
    summary="Get Cart",
    description="Fetch the active cart for the signed-in user or for a guest (using X-Guest-Token). Returns an empty cart plus a guest_token when none exists.",
    responses={
        "200": CartData,
        "500": None,
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
    description="Add a product variant to the cart. Works for guests (pass guest_token) and authenticated users.",
    responses={
        "200": CartItemData,
        "400": ValidationErrorData,
        "404": None,
        "500": None,
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
    description="Update quantity of a cart item. Validates ownership via user or guest_token.",
    responses={
        "200": CartItemData,
        "400": ValidationErrorData,
        "403": None,
        "404": None,
        "500": None,
    },
)
def update_item(item_id: str):
    """Update cart item quantity."""
    return CartController.update_item(item_id)


@bp.delete("/items/<item_id>")
@endpoint(
    tags=["Cart"],
    summary="Remove Cart Item",
    description="Remove an item from the cart. Validates ownership via user or guest_token.",
    responses={
        "200": None,
        "403": None,
        "404": None,
        "500": None,
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
    description="Estimate discount from loyalty points without charging. Requires authentication; redemption happens at checkout.",
    responses={
        "200": CartData,
        "400": ValidationErrorData,
        "401": None,
        "404": None,
        "500": None,
    },
)
def apply_points():
    """Apply loyalty points to cart."""
    return CartController.apply_points()




