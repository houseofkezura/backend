"""
Public wishlist routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme, QueryParameter
from app.schemas.response_data import (
    WishlistItemData,
    WishlistListData,
    WishlistCheckData,
    ValidationErrorData,
)
from app.schemas.wishlist import AddWishlistItemRequest
from .controllers import WishlistController
from . import bp
from app.utils.decorators.auth import customer_required


@bp.get("")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Wishlist"],
    summary="Get Wishlist",
    description="Retrieve all saved product variants in the authenticated user's wishlist. Returns paginated results with product details including pricing, stock status, and variant attributes. Use this to display the user's saved favorites on their account page or wishlist view.",
    query_params=[
        QueryParameter("page", "integer", required=False, description="Page number for pagination", default=1),
        QueryParameter("per_page", "integer", required=False, description="Number of items per page (max 100)", default=20),
    ],
    responses={
        "200": WishlistListData,
        "401": None,
        "500": None,
    },
)
def get_wishlist():
    """Get all wishlist items for the current user."""
    return WishlistController.get_wishlist()


@bp.post("/items")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=AddWishlistItemRequest,
    tags=["Wishlist"],
    summary="Add Item to Wishlist",
    description="Save a product variant to the user's wishlist for later purchase. If the variant is already saved, returns the existing item without error. This enables the 'Save for Later' feature on product pages, allowing customers to bookmark items they're interested in but not ready to buy immediately.",
    responses={
        "200": WishlistItemData,
        "400": ValidationErrorData,
        "401": None,
        "404": None,
        "500": None,
    },
)
def add_item():
    """Add a product variant to wishlist."""
    return WishlistController.add_item()


@bp.delete("/items/<item_id>")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Wishlist"],
    summary="Remove Item from Wishlist",
    description="Remove a saved product variant from the user's wishlist. The item_id is the wishlist item ID (not the variant ID). Use this when a user clicks 'Remove from Wishlist' or decides they no longer want to save an item. Only the owner of the wishlist item can remove it.",
    responses={
        "200": None,
        "401": None,
        "403": None,
        "404": None,
        "500": None,
    },
)
def remove_item(item_id: str):
    """Remove an item from wishlist."""
    return WishlistController.remove_item(item_id)


@bp.get("/check/<variant_id>")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Wishlist"],
    summary="Check if Variant is in Wishlist",
    description="Check whether a specific product variant is currently saved in the authenticated user's wishlist. Returns a boolean flag and the wishlist item ID if found. Use this on product detail pages to show the correct 'Add to Wishlist' vs 'Remove from Wishlist' button state without loading the entire wishlist.",
    responses={
        "200": WishlistCheckData,
        "401": None,
        "404": None,
        "500": None,
    },
)
def check_item(variant_id: str):
    """Check if a variant is in the user's wishlist."""
    return WishlistController.check_item(variant_id)

