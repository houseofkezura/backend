"""
Checkout orchestration service.

Handles the complete checkout flow including:
- Cart validation
- Inventory reservation
- Shipping calculation
- Payment processing
- Order creation
- Auto-account creation for qualifying guest orders
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from dataclasses import dataclass
from decimal import Decimal
import secrets
import string
import uuid

from flask import current_app
from sqlalchemy.exc import IntegrityError

from ...extensions import db
from ...models.cart import Cart, CartItem
from ...models.order import Order, OrderItem
from ...models.product import ProductVariant, Inventory
from ...models.user import AppUser, Profile, Address
from ...models.role import Role, UserRole
from ...enums.orders import OrderStatus
from ...enums.auth import RoleNames
from ...utils.auth.clerk import create_clerk_user
from ...logging import log_error, log_event
from config import Config


@dataclass
class CheckoutRequest:
    """Request data for checkout."""
    cart_id: Optional[str] = None
    guest_token: Optional[str] = None
    shipping_address: Dict[str, Any] = None
    shipping_method: Optional[str] = None
    payment_method: str = "card"
    payment_token: Optional[str] = None
    apply_points: bool = False
    points_to_redeem: int = 0
    idempotency_key: Optional[str] = None
    # Guest checkout fields
    email: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


@dataclass
class CheckoutResult:
    """Result of checkout processing."""
    success: bool
    order_id: Optional[str] = None
    payment_status: Optional[str] = None
    error: Optional[str] = None
    auto_account_created: bool = False
    clerk_id: Optional[str] = None


def generate_default_password(length: int = 16) -> str:
    """Generate a random default password."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def calculate_shipping_cost(country: str, weight_g: int, method: str = "standard") -> float:
    """
    Calculate shipping cost based on zone and method.
    
    Simplified implementation - in production, this would query shipping zones.
    """
    # Zone 1: Nigeria
    if country.upper() == "NG" or country.upper() == "NIGERIA":
        if method == "express":
            return 5000.0  # ₦5,000
        return 3000.0  # ₦3,000 standard
    
    # Zone 2: Rest of Africa
    african_countries = ["GH", "KE", "ZA", "EG", "ET", "TZ", "UG", "RW", "ZM", "ZW"]
    if country.upper() in african_countries:
        if method == "express":
            return 15000.0
        return 10000.0
    
    # Zone 3: International
    if method == "express":
        return 25000.0
    return 20000.0


def process_checkout(request: CheckoutRequest, current_user: Optional[AppUser] = None) -> CheckoutResult:
    """
    Process checkout orchestration.
    
    This function handles:
    1. Cart validation
    2. Inventory reservation
    3. Shipping calculation
    4. Order creation
    5. Payment processing
    6. Auto-account creation for qualifying guest orders (₦200k-₦500k)
    
    Args:
        request: Checkout request data
        current_user: Authenticated user (None for guest checkout)
        
    Returns:
        CheckoutResult with order details or error
    """
    try:
        # Step 1: Load cart
        cart = None
        if current_user:
            cart = Cart.query.filter_by(user_id=current_user.id).first()
        elif request.guest_token:
            cart = Cart.query.filter_by(guest_token=request.guest_token).first()
        elif request.cart_id:
            try:
                cart_uuid = uuid.UUID(request.cart_id)
                cart = Cart.query.get(cart_uuid)
            except ValueError:
                pass
        
        if not cart or not cart.items:
            return CheckoutResult(success=False, error="Cart is empty or not found")
        
        # Step 2: Validate inventory and calculate totals
        subtotal = 0.0
        items_to_order = []
        
        for cart_item in cart.items:
            variant = ProductVariant.query.get(cart_item.variant_id)
            if not variant:
                return CheckoutResult(success=False, error=f"Variant {cart_item.variant_id} not found")
            
            # Check inventory
            if variant.inventory and variant.inventory.quantity < cart_item.quantity:
                return CheckoutResult(
                    success=False,
                    error=f"Insufficient stock for {variant.sku}. Available: {variant.inventory.quantity}"
                )
            
            line_total = cart_item.quantity * float(cart_item.unit_price)
            subtotal += line_total
            
            items_to_order.append({
                "variant": variant,
                "quantity": cart_item.quantity,
                "unit_price": float(cart_item.unit_price),
            })
        
        # Step 3: Calculate shipping
        country = request.shipping_address.get("country", "NG") if request.shipping_address else "NG"
        total_weight = sum(item["variant"].weight_g or 0 for item in items_to_order)
        shipping_cost = calculate_shipping_cost(country, total_weight, request.shipping_method or "standard")
        
        # Step 4: Calculate discount and points redemption
        discount = 0.0
        points_redeemed = 0
        
        if request.apply_points and request.points_to_redeem > 0:
            # Simple points redemption: 1 point = ₦10
            points_discount = min(request.points_to_redeem * 10, subtotal * 0.5)  # Max 50% discount
            discount = points_discount
            points_redeemed = int(points_discount / 10)
        
        # Step 5: Calculate total
        total = subtotal + shipping_cost - discount
        
        # Step 6: Create provisional order
        order = Order()
        order.user_id = current_user.id if current_user else None
        order.status = OrderStatus.PENDING_PAYMENT
        order.subtotal = Decimal(str(subtotal))
        order.shipping_cost = Decimal(str(shipping_cost))
        order.discount = Decimal(str(discount))
        order.points_redeemed = points_redeemed
        order.total = Decimal(str(total))
        order.amount = Decimal(str(total))  # Legacy field
        order.currency = "NGN"
        order.shipping_address = request.shipping_address or {}
        order.guest_email = request.email
        order.guest_phone = request.phone
        
        db.session.add(order)
        db.session.flush()
        
        # Create order items
        for item_data in items_to_order:
            order_item = OrderItem()
            order_item.order_id = order.id
            order_item.variant_id = item_data["variant"].id
            order_item.quantity = item_data["quantity"]
            order_item.unit_price = Decimal(str(item_data["unit_price"]))
            db.session.add(order_item)
        
        db.session.commit()
        
        # Step 7: Process payment (simplified - in production, use payment gateway)
        # For MVP, we'll mark as paid if payment_token is provided
        payment_success = False
        if request.payment_token:
            # In production, call payment gateway here
            # For now, simulate success
            payment_success = True
        
        if not payment_success:
            order.status = OrderStatus.FAILED
            db.session.commit()
            return CheckoutResult(success=False, error="Payment failed")
        
        # Step 8: Finalize order and decrement inventory
        order.status = OrderStatus.PAID
        db.session.commit()
        
        # Decrement inventory
        for item_data in items_to_order:
            variant = item_data["variant"]
            if variant.inventory:
                variant.inventory.quantity -= item_data["quantity"]
                db.session.commit()
        
        # Step 9: Auto-account creation for guest orders (₦200k-₦500k)
        auto_account_created = False
        clerk_id = None
        
        total_float = float(total)
        if not current_user and request.email and 200000 <= total_float <= 500000:
            # Check if user already exists
            existing_user = AppUser.query.filter_by(email=request.email).first()
            
            if not existing_user:
                # Generate default password
                default_password = generate_default_password()
                
                # Create Clerk user
                clerk_user_data = create_clerk_user(
                    email=request.email,
                    password=default_password,
                    first_name=request.first_name,
                    last_name=request.last_name,
                    phone=request.phone,
                    skip_password_checks=True,
                )
                
                if clerk_user_data:
                    clerk_id = clerk_user_data["clerk_id"]
                    
                    # Create AppUser
                    app_user = AppUser()
                    app_user.clerk_id = clerk_id
                    app_user.email = request.email
                    
                    db.session.add(app_user)
                    db.session.flush()
                    
                    # Create Profile
                    profile = Profile()
                    profile.firstname = request.first_name or ""
                    profile.lastname = request.last_name or ""
                    profile.phone = request.phone
                    profile.user_id = app_user.id
                    db.session.add(profile)
                    
                    # Create Address
                    address = Address()
                    address.user_id = app_user.id
                    if request.shipping_address:
                        address.country = request.shipping_address.get("country")
                        address.state = request.shipping_address.get("state")
                    db.session.add(address)
                    
                    # Create Loyalty Account (Muse tier)
                    from ...models.loyalty import LoyaltyAccount
                    loyalty_account = LoyaltyAccount()
                    loyalty_account.user_id = app_user.id
                    loyalty_account.tier = "Muse"
                    loyalty_account.points_balance = 0
                    loyalty_account.lifetime_spend = Decimal(str(total_float))
                    db.session.add(loyalty_account)
                    
                    # Assign CUSTOMER role
                    role = Role.query.filter_by(name=RoleNames.CUSTOMER).first()
                    if role:
                        UserRole.assign_role(app_user, role, commit=False)
                    
                    # Link order to new user
                    order.user_id = app_user.id
                    
                    db.session.commit()
                    
                    auto_account_created = True
                    log_event(f"Auto-created account for guest order: {order.id}, Clerk ID: {clerk_id}")
                    
                    # TODO: Send welcome email with default password and account details
            else:
                # Link order to existing user
                order.user_id = existing_user.id
                db.session.commit()
        
        log_event(f"Checkout completed: Order {order.id}, Total: {total}")
        
        return CheckoutResult(
            success=True,
            order_id=str(order.id),
            payment_status="paid",
            auto_account_created=auto_account_created,
            clerk_id=clerk_id,
        )
        
    except IntegrityError as e:
        db.session.rollback()
        log_error("Database integrity error during checkout", error=e)
        return CheckoutResult(success=False, error="Checkout failed due to database error")
    except Exception as e:
        db.session.rollback()
        log_error("Checkout processing failed", error=e)
        return CheckoutResult(success=False, error=f"Checkout failed: {str(e)}")

