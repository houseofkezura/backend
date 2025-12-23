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
    
    IMPORTANT: This function preserves guest_token. If a guest_token is provided,
    it will use that token. If no token is provided and user is guest, it generates a new one.
    The token should be persisted by the frontend and reused across requests.
    
    For authenticated users: If a guest_token is provided and a guest cart exists,
    the guest cart items will be migrated to the user's cart (if user cart exists)
    or the guest cart will be converted to the user's cart.
    
    Args:
        user_id: Authenticated user ID (None for guests)
        guest_token: Guest cart token (None for authenticated users, but can be provided for migration)
        
    Returns:
        Cart instance
    """
    if user_id:
        # For authenticated users, ALWAYS prioritize user cart
        log_event(f"get_or_create_cart: Authenticated user {user_id}, guest_token provided: {bool(guest_token)}")
        # First, try to find existing user cart
        user_cart = Cart.query.filter_by(user_id=user_id).first()
        log_event(f"get_or_create_cart: Existing user cart found: {bool(user_cart)}, Cart ID: {user_cart.id if user_cart else None}")
        
        # If guest_token provided, check for guest cart to migrate
        if guest_token and not user_cart:
            guest_cart = Cart.query.filter_by(guest_token=guest_token).first()
            if guest_cart:
                # Migrate guest cart to user cart
                log_event(f"get_or_create_cart: Migrating guest cart {guest_cart.id} to user {user_id}")
                guest_cart.user_id = user_id
                guest_cart.guest_token = None  # Clear guest token after migration
                db.session.commit()
                log_event(f"Migrated guest cart {guest_cart.id} to user {user_id}")
                return guest_cart
        
        # If user cart exists and guest cart exists, merge items
        if user_cart and guest_token:
            guest_cart = Cart.query.filter_by(guest_token=guest_token).first()
            if guest_cart and guest_cart.id != user_cart.id:
                # Merge guest cart items into user cart
                guest_items = list(guest_cart.items)  # Get copy of items before modifying
                for guest_item in guest_items:
                    # Check if variant already exists in user cart
                    existing_item = CartItem.query.filter_by(
                        cart_id=user_cart.id,
                        variant_id=guest_item.variant_id
                    ).first()
                    
                    if existing_item:
                        # Update quantity
                        existing_item.quantity += guest_item.quantity
                        # Delete the guest item since we've merged it
                        db.session.delete(guest_item)
                    else:
                        # Move item to user cart
                        guest_item.cart_id = user_cart.id
                
                # Delete guest cart after migration (items already moved or deleted)
                db.session.delete(guest_cart)
                db.session.commit()
                log_event(f"Merged guest cart {guest_cart.id} into user cart {user_cart.id} for user {user_id}")
                # Refresh to get updated items
                db.session.refresh(user_cart)
        
        # If no user cart exists, create one
        # IMPORTANT: For authenticated users, we ALWAYS create a cart with user_id
        # We NEVER create a guest cart for authenticated users, even if guest_token is provided
        if not user_cart:
            log_event(f"get_or_create_cart: No user cart found, creating new cart for user {user_id}")
            user_cart = Cart()
            user_cart.user_id = user_id
            # Explicitly set guest_token to None for authenticated users
            # This ensures the cart is always associated with the user, not a guest token
            user_cart.guest_token = None
            db.session.add(user_cart)
            db.session.flush()  # Flush to get the ID
            db.session.commit()
            log_event(f"Created new cart {user_cart.id} for authenticated user {user_id} - user_id: {user_cart.user_id}, guest_token: {user_cart.guest_token}")
        
        # CRITICAL: Double-check that the cart is properly associated with the user
        # This prevents any edge cases where a cart might not have the correct user_id
        if user_cart.user_id != user_id:
            log_error(f"Cart {user_cart.id} has wrong user_id {user_cart.user_id}, expected {user_id}. Fixing...", error=None)
            user_cart.user_id = user_id
            user_cart.guest_token = None  # Ensure guest_token is cleared
            db.session.commit()
            log_event(f"Fixed cart {user_cart.id} to be associated with user {user_id}")
        
        # Final verification log
        log_event(f"get_or_create_cart: Returning cart {user_cart.id} for user {user_id} - cart.user_id: {user_cart.user_id}, cart.guest_token: {user_cart.guest_token}")
        return user_cart
    elif guest_token:
        # Always use the provided guest_token - don't generate a new one
        cart = Cart.query.filter_by(guest_token=guest_token).first()
        if not cart:
            cart = Cart()
            cart.guest_token = guest_token
            db.session.add(cart)
            db.session.commit()
        return cart
    else:
        # Only generate new token if no token was provided
        # This should rarely happen if frontend properly manages tokens
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
        Can also get cart by ID or guest_token as query parameters.
        
        Uses get_or_create_cart() for consistency with add_item() to ensure
        authenticated users always get their cart properly.
        """
        try:
            current_user = get_current_user()
            
            # Log authentication status
            auth_token = request.headers.get("Authorization", "")
            has_auth_header = bool(auth_token and auth_token.startswith("Bearer "))
            log_event(f"Get cart request - Authenticated: {bool(current_user)}, Has Auth Header: {has_auth_header}, User ID: {current_user.id if current_user else None}")
            
            # Check for cart_id or guest_token in query params (for direct cart lookup)
            cart_id = request.args.get("cart_id")
            guest_token = request.headers.get("X-Guest-Token") or request.args.get("guest_token")
            
            cart = None
            
            # Priority: cart_id > user_id > guest_token
            if cart_id:
                try:
                    cart_uuid = uuid.UUID(cart_id)
                    cart: Cart = Cart.query.get(cart_uuid)
                    if cart:
                        # Verify ownership - CRITICAL: For authenticated users, cart MUST have matching user_id
                        if current_user:
                            if cart.user_id != current_user.id:
                                log_error(f"Cart ownership mismatch: Cart {cart.id} has user_id {cart.user_id}, but current user is {current_user.id}", error=None)
                                return error_response("Unauthorized access to cart", 403)
                            # Also verify it's not a guest cart (shouldn't have guest_token for authenticated users)
                            if cart.guest_token and not cart.user_id:
                                log_error(f"Cart {cart.id} is a guest cart but user is authenticated", error=None)
                                return error_response("Unauthorized access to cart", 403)
                        elif not current_user:
                            # For guests, verify guest_token matches
                            if cart.guest_token != guest_token:
                                return error_response("Unauthorized access to cart", 403)
                            # Guest shouldn't access user carts
                            if cart.user_id:
                                return error_response("Unauthorized access to cart", 403)
                except ValueError:
                    return error_response("Invalid cart ID format", 400)
            elif current_user:
                # Use get_or_create_cart() for consistency with add_item()
                # This ensures authenticated users always get their cart properly
                # For authenticated users, guest_token is only used for migration
                cart = get_or_create_cart(
                    user_id=current_user.id,
                    guest_token=guest_token  # Allow migration if guest_token provided
                )
                # Verify cart is properly associated with user
                if cart and cart.user_id != current_user.id:
                    log_error(f"Cart {cart.id} is not associated with user {current_user.id}. Cart user_id: {cart.user_id}", error=None)
                    # Force create a new cart for the user
                    cart = Cart()
                    cart.user_id = current_user.id
                    cart.guest_token = None
                    db.session.add(cart)
                    db.session.commit()
                    log_event(f"Created new cart {cart.id} for user {current_user.id} due to mismatch")
                # Log for debugging
                if cart:
                    log_event(f"Get cart: User {current_user.id}, Cart {cart.id}, Cart user_id: {cart.user_id}, Cart guest_token: {cart.guest_token}, Items count: {len(cart.items)}")
                else:
                    log_event(f"Get cart: User {current_user.id}, No cart found - will create new one")
            elif guest_token:
                log_event(f"Get cart: Guest request, guest_token: {guest_token[:10] if guest_token else None}...")
                cart = get_or_create_cart(guest_token=guest_token)
            else:
                # No user, no token - create new guest cart
                log_event(f"Get cart: No user, no token - creating new guest cart")
                cart = get_or_create_cart()
                guest_token = cart.guest_token
            
            if not cart:
                # This should rarely happen, but handle gracefully
                log_error("Failed to get or create cart", error=None)
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
                        "guest_token": guest_token if guest_token else generate_guest_token(),
                    }
                )
            
            # Refresh cart to ensure items are loaded
            db.session.refresh(cart)
            
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
            
            # Log authentication status
            auth_token = request.headers.get("Authorization", "")
            has_auth_header = bool(auth_token and auth_token.startswith("Bearer "))
            log_event(f"Add item request - Authenticated: {bool(current_user)}, Has Auth Header: {has_auth_header}, User ID: {current_user.id if current_user else None}")
            
            # For authenticated users, we should NOT use guest_token from payload/header
            # Guest token is only used for migration if provided
            # For authenticated users, cart is always associated with user_id
            guest_token = None
            if not current_user:
                # Only use guest_token for guests
                guest_token = payload.guest_token or request.headers.get("X-Guest-Token")
                log_event(f"Guest request - Using guest_token: {bool(guest_token)}")
            elif payload.guest_token or request.headers.get("X-Guest-Token"):
                # For authenticated users, guest_token is only for migration
                guest_token = payload.guest_token or request.headers.get("X-Guest-Token")
                log_event(f"Authenticated user with guest_token for migration - User: {current_user.id}, Guest token: {guest_token[:10] if guest_token else None}...")
            
            # Get or create cart
            cart = get_or_create_cart(
                user_id=current_user.id if current_user else None,
                guest_token=guest_token
            )
            
            # Log cart details
            if current_user:
                log_event(f"Add item: User {current_user.id}, Cart {cart.id}, Cart user_id: {cart.user_id}, Cart guest_token: {cart.guest_token}")
            else:
                log_event(f"Add item: Guest, Cart {cart.id}, Cart user_id: {cart.user_id}, Cart guest_token: {cart.guest_token}")
            
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
            
            # Reload cart to ensure items are properly loaded
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







