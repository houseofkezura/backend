"""
Wishlist controller for public wishlist endpoints.
"""

from __future__ import annotations

from flask import Response, request
from typing import Optional
import uuid

from app.extensions import db
from app.models.wishlist import WishlistItem
from app.models.product import ProductVariant
from app.schemas.wishlist import AddWishlistItemRequest
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class WishlistController:
    """Controller for public wishlist endpoints."""

    @staticmethod
    def get_wishlist() -> Response:
        """
        Get the current user's wishlist.
        
        Returns all saved product variants for the authenticated user.
        Requires authentication.
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            # Get pagination parameters
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 20, type=int)
            per_page = max(1, min(per_page, 100))  # Limit between 1 and 100
            
            # Query wishlist items
            query = WishlistItem.query.filter_by(user_id=current_user.id)
            query = query.order_by(WishlistItem.created_at.desc())
            
            # Paginate
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            items: list[WishlistItem] = pagination.items
            
            return success_response(
                "Wishlist retrieved successfully",
                200,
                {
                    "items": [item.to_dict() for item in items],
                    "total": pagination.total,
                    "current_page": pagination.page,
                    "total_pages": pagination.pages,
                }
            )
        except Exception as e:
            log_error("Failed to get wishlist", error=e)
            return error_response("Failed to retrieve wishlist", 500)

    @staticmethod
    def add_item() -> Response:
        """
        Add a product variant to the wishlist.
        
        If the variant is already in the wishlist, returns success without error.
        Requires authentication.
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            payload = AddWishlistItemRequest.model_validate(request.get_json())
            
            # Validate variant ID
            try:
                variant_id = uuid.UUID(payload.variant_id)
            except ValueError:
                return error_response("Invalid variant ID format", 400)
            
            # Check if variant exists
            variant = ProductVariant.query.get(variant_id)
            if not variant:
                return error_response("Variant not found", 404)
            
            # Check if already in wishlist
            existing_item = WishlistItem.query.filter_by(
                user_id=current_user.id,
                variant_id=variant_id
            ).first()
            
            if existing_item:
                return success_response(
                    "Item already in wishlist",
                    200,
                    {"item": existing_item.to_dict()}
                )
            
            # Create wishlist item
            wishlist_item = WishlistItem()
            wishlist_item.user_id = current_user.id
            wishlist_item.variant_id = variant_id
            
            db.session.add(wishlist_item)
            db.session.commit()
            
            log_event(f"Added variant {variant_id} to wishlist for user {current_user.id}")
            
            return success_response(
                "Item added to wishlist successfully",
                200,
                {"item": wishlist_item.to_dict()}
            )
        except Exception as e:
            log_error("Failed to add item to wishlist", error=e)
            db.session.rollback()
            return error_response("Failed to add item to wishlist", 500)

    @staticmethod
    def remove_item(item_id: str) -> Response:
        """
        Remove an item from the wishlist.
        
        Args:
            item_id: Wishlist item ID
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                item_uuid = uuid.UUID(item_id)
            except ValueError:
                return error_response("Invalid item ID format", 400)
            
            # Find wishlist item
            wishlist_item = WishlistItem.query.get(item_uuid)
            if not wishlist_item:
                return error_response("Wishlist item not found", 404)
            
            # Verify ownership
            if wishlist_item.user_id != current_user.id:
                return error_response("Unauthorized", 403)
            
            db.session.delete(wishlist_item)
            db.session.commit()
            
            log_event(f"Removed wishlist item {item_id} for user {current_user.id}")
            
            return success_response("Item removed from wishlist successfully", 200)
        except Exception as e:
            log_error("Failed to remove item from wishlist", error=e)
            db.session.rollback()
            return error_response("Failed to remove item from wishlist", 500)

    @staticmethod
    def check_item(variant_id: str) -> Response:
        """
        Check if a variant is in the user's wishlist.
        
        Args:
            variant_id: Product variant ID to check
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                variant_uuid = uuid.UUID(variant_id)
            except ValueError:
                return error_response("Invalid variant ID format", 400)
            
            # Check if variant exists
            variant = ProductVariant.query.get(variant_uuid)
            if not variant:
                return error_response("Variant not found", 404)
            
            # Check if in wishlist
            wishlist_item = WishlistItem.query.filter_by(
                user_id=current_user.id,
                variant_id=variant_uuid
            ).first()
            
            return success_response(
                "Check completed",
                200,
                {
                    "variant_id": variant_id,
                    "is_in_wishlist": wishlist_item is not None,
                    "wishlist_item_id": str(wishlist_item.id) if wishlist_item else None,
                }
            )
        except Exception as e:
            log_error("Failed to check wishlist item", error=e)
            return error_response("Failed to check wishlist item", 500)

