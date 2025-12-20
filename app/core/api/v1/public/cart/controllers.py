"""
Cart controller for public cart endpoints.
"""

from __future__ import annotations

from flask import Response, request, g
from typing import Optional
import uuid
import secrets
import string

from app.extensions import db
from app.models.cart import Cart, CartItem
from app.models.product import ProductVariant, Inventory
from app.schemas.cart import AddCartItemRequest, UpdateCartItemRequest, ApplyPointsRequest
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


def generate_guest_token() -> str:
    """Generate a unique guest cart token."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))


def get_or_create_cart(user_id: Optional[uuid.UUID] = None, guest_token: Optional[str] = None) -> Cart:
    """
    Get existing cart or create a new one.
    
    Args:
        user_id: Authenticated user ID (None for guests)
        guest_token: Guest cart token (None for authenticated users)
        
    Returns:
        Cart instance
    """
    if user_id:
        cart = Cart.query.filter_by(user_id=user_id).first()
        if not cart:
            cart = Cart()
            cart.user_id = user_id
            db.session.add(cart)
            db.session.commit()
        return cart
    elif guest_token:
        cart = Cart.query.filter_by(guest_token=guest_token).first()
        if not cart:
            cart = Cart()
            cart.guest_token = guest_token
            db.session.add(cart)
            db.session.commit()
        return cart
    else:
        # Create new guest cart
        cart = Cart()
        cart.guest_token = generate_guest_token()
        db.session.add(cart)
        db.session.commit()
        return cart


class CartController:
    """Controller for public cart endpoints."""

    @staticmethod
    def get_cart() -> Response:
        """
        Get the current user's cart or guest cart.
        
        Supports both authenticated users and guests.
        """
        try:
            current_user = get_current_user()
            guest_token = request.headers.get("X-Guest-Token") or request.args.get("guest_token")
            
            cart = None
            if current_user:
                cart = Cart.query.filter_by(user_id=current_user.id).first()
            elif guest_token:
                cart = Cart.query.filter_by(guest_token=guest_token).first()
            
            if not cart:
                # Return empty cart structure
                return success_response(
                    "Cart retrieved successfully",
                    200,
                    {
                        "cart": {
                            "id": None,
                            "items": [],
                            "total_items": 0,
                            "subtotal": 0.0,
                        },
                        "guest_token": guest_token or generate_guest_token(),
                    }
                )
            
            return success_response(
                "Cart retrieved successfully",
                200,
                {
                    "cart": cart.to_dict(),
                    "guest_token": cart.guest_token,
                }
            )
        except Exception as e:
            log_error("Failed to get cart", error=e)
            return error_response("Failed to retrieve cart", 500)

    @staticmethod
    def add_item() -> Response:
        """
        Add an item to the cart.
        
        Supports both authenticated users and guests.
        """
        try:
            payload = AddCartItemRequest.model_validate(request.get_json())
            current_user = get_current_user()
            
            # Get or create cart
            cart = get_or_create_cart(
                user_id=current_user.id if current_user else None,
                guest_token=payload.guest_token or request.headers.get("X-Guest-Token")
            )
            
            # Validate variant
            try:
                variant_id = uuid.UUID(payload.variant_id)
            except ValueError:
                return error_response("Invalid variant ID format", 400)
            
            variant = ProductVariant.query.get(variant_id)
            if not variant:
                return error_response("Variant not found", 404)
            
            # Check inventory
            if variant.inventory and variant.inventory.quantity < payload.quantity:
                return error_response(
                    f"Insufficient stock. Available: {variant.inventory.quantity}",
                    400
                )
            
            # Check if item already exists in cart
            existing_item = CartItem.query.filter_by(
                cart_id=cart.id,
                variant_id=variant_id
            ).first()
            
            if existing_item:
                # Update quantity
                existing_item.quantity += payload.quantity
                db.session.commit()
            else:
                # Create new cart item
                cart_item = CartItem()
                cart_item.cart_id = cart.id
                cart_item.variant_id = variant_id
                cart_item.quantity = payload.quantity
                cart_item.unit_price = variant.price_ngn
                db.session.add(cart_item)
                db.session.commit()
            
            # Reload cart
            db.session.refresh(cart)
            
            return success_response(
                "Item added to cart successfully",
                200,
                {
                    "cart": cart.to_dict(),
                    "guest_token": cart.guest_token,
                }
            )
        except Exception as e:
            log_error("Failed to add item to cart", error=e)
            db.session.rollback()
            return error_response("Failed to add item to cart", 500)

    @staticmethod
    def update_item(item_id: str) -> Response:
        """
        Update a cart item quantity.
        
        Args:
            item_id: Cart item ID
        """
        try:
            payload = UpdateCartItemRequest.model_validate(request.get_json())
            current_user = get_current_user()
            guest_token = request.headers.get("X-Guest-Token") or request.args.get("guest_token")
            
            try:
                item_uuid = uuid.UUID(item_id)
            except ValueError:
                return error_response("Invalid item ID format", 400)
            
            # Find cart item
            cart_item = CartItem.query.get(item_uuid)
            if not cart_item:
                return error_response("Cart item not found", 404)
            
            # Verify cart ownership
            cart = cart_item.cart
            if current_user and cart.user_id != current_user.id:
                return error_response("Unauthorized", 403)
            if not current_user and cart.guest_token != guest_token:
                return error_response("Unauthorized", 403)
            
            # Check inventory
            variant = cart_item.variant
            if variant.inventory and variant.inventory.quantity < payload.quantity:
                return error_response(
                    f"Insufficient stock. Available: {variant.inventory.quantity}",
                    400
                )
            
            cart_item.quantity = payload.quantity
            db.session.commit()
            
            db.session.refresh(cart)
            
            return success_response(
                "Cart item updated successfully",
                200,
                {"cart": cart.to_dict()}
            )
        except Exception as e:
            log_error("Failed to update cart item", error=e)
            db.session.rollback()
            return error_response("Failed to update cart item", 500)

    @staticmethod
    def delete_item(item_id: str) -> Response:
        """
        Remove an item from the cart.
        
        Args:
            item_id: Cart item ID
        """
        try:
            current_user = get_current_user()
            guest_token = request.headers.get("X-Guest-Token") or request.args.get("guest_token")
            
            try:
                item_uuid = uuid.UUID(item_id)
            except ValueError:
                return error_response("Invalid item ID format", 400)
            
            cart_item = CartItem.query.get(item_uuid)
            if not cart_item:
                return error_response("Cart item not found", 404)
            
            # Verify cart ownership
            cart = cart_item.cart
            if current_user and cart.user_id != current_user.id:
                return error_response("Unauthorized", 403)
            if not current_user and cart.guest_token != guest_token:
                return error_response("Unauthorized", 403)
            
            db.session.delete(cart_item)
            db.session.commit()
            
            db.session.refresh(cart)
            
            return success_response(
                "Item removed from cart successfully",
                200,
                {"cart": cart.to_dict()}
            )
        except Exception as e:
            log_error("Failed to delete cart item", error=e)
            db.session.rollback()
            return error_response("Failed to remove item from cart", 500)

    @staticmethod
    def apply_points() -> Response:
        """
        Apply loyalty points to cart (calculate discount).
        
        This endpoint calculates the feasible redemption and returns new totals.
        Actual redemption happens at checkout.
        """
        try:
            payload = ApplyPointsRequest.model_validate(request.get_json())
            current_user = get_current_user()
            guest_token = payload.guest_token or request.headers.get("X-Guest-Token")
            
            if not current_user:
                return error_response("Loyalty points can only be applied by authenticated users", 401)
            
            # Get cart
            cart = Cart.query.filter_by(user_id=current_user.id).first()
            if not cart or not cart.items:
                return error_response("Cart is empty", 400)
            
            # Get loyalty account
            from app.models.loyalty import LoyaltyAccount
            loyalty_account = LoyaltyAccount.query.filter_by(user_id=current_user.id).first()
            
            if not loyalty_account:
                return error_response("No loyalty account found", 404)
            
            if loyalty_account.points_balance < payload.points_to_redeem:
                return error_response(
                    f"Insufficient points. Available: {loyalty_account.points_balance}",
                    400
                )
            
            # Calculate discount (1 point = ₦10)
            points_discount = min(payload.points_to_redeem * 10, cart.subtotal * 0.5)  # Max 50% discount
            new_subtotal = cart.subtotal - points_discount
            
            return success_response(
                "Points application calculated",
                200,
                {
                    "original_subtotal": cart.subtotal,
                    "points_redeemed": int(points_discount / 10),
                    "discount": points_discount,
                    "new_subtotal": new_subtotal,
                    "remaining_points": loyalty_account.points_balance - int(points_discount / 10),
                }
            )
        except Exception as e:
            log_error("Failed to apply points", error=e)
            return error_response("Failed to apply points", 500)







