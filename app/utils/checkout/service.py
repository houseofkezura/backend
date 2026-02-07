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
from ...enums.payments import PaymentType
from ...utils.payments.payment_manager import PaymentManager
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
    authorization_url: Optional[str] = None
    payment_reference: Optional[str] = None
    error: Optional[str] = None
    auto_account_created: bool = False
    clerk_id: Optional[str] = None


def generate_default_guest_password() -> str:
    """
    Generate a secure default password for auto-created guest accounts.
    
    Format: {DEFAULT_GUEST_PREFIX}_{random_string}
    Uses cryptographically secure random generation.
    
    Returns:
        A password string with prefix and random suffix
    """
    from config import Config
    
    # Generate random suffix (16 characters: alphanumeric + some special chars)
    alphabet = string.ascii_letters + string.digits
    random_suffix = ''.join(secrets.choice(alphabet) for _ in range(16))
    
    prefix = Config.DEFAULT_GUEST_PREFIX or "kezura"
    return f"{prefix}_{random_suffix}"


def calculate_shipping_cost(country: str, weight_g: int, method: str = "standard") -> float:
    """
    Calculate shipping cost based on zone and method.
    
    NOTE: Shipping cost is DISABLED for now until exact costs are confirmed.
    Returns 0 for all orders.
    """
    # Shipping disabled until we have confirmed rates
    return 0.0
    
    # TODO: Re-enable when shipping rates are confirmed
    # Zone 1: Nigeria
    # if country.upper() == "NG" or country.upper() == "NIGERIA":
    #     if method == "express":
    #         return 5000.0  # ₦5,000
    #     return 3000.0  # ₦3,000 standard
    # 
    # # Zone 2: Rest of Africa
    # african_countries = ["GH", "KE", "ZA", "EG", "ET", "TZ", "UG", "RW", "ZM", "ZW"]
    # if country.upper() in african_countries:
    #     if method == "express":
    #         return 15000.0
    #     return 10000.0
    # 
    # # Zone 3: International
    # if method == "express":
    #     return 25000.0
    # return 20000.0


def process_checkout(request: CheckoutRequest, current_user: Optional[AppUser] = None) -> CheckoutResult:
    """
    Process checkout orchestration.
    
    This function handles:
    1. Idempotency check (if idempotency_key provided)
    2. Cart validation
    3. Inventory reservation
    4. Shipping calculation
    5. Order creation
    6. Payment processing
    7. Auto-account creation for qualifying guest orders (₦200k-₦500k)
    8. Notification hooks
    
    Args:
        request: Checkout request data
        current_user: Authenticated user (None for guest checkout)
        
    Returns:
        CheckoutResult with order details or error
    """
    try:
        # Idempotency check: if key provided, check cache for existing result
        if request.idempotency_key:
            from ...extensions import app_cache
            cache_key = f"checkout:idempotency:{request.idempotency_key}"
            cached_result = app_cache.get(cache_key)
            if cached_result:
                log_event(f"Idempotent checkout request: {request.idempotency_key}")
                return CheckoutResult(**cached_result)
        
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
        
        # Step 6: Create provisional order with unique order number
        order = Order()
        order.order_number = Order.generate_order_number()
        order.user_id = current_user.id if current_user else None
        order.status = str(OrderStatus.PENDING_PAYMENT)
        order.subtotal = Decimal(str(subtotal))
        order.shipping_cost = Decimal(str(shipping_cost))
        order.discount = Decimal(str(discount))
        order.points_redeemed = points_redeemed
        order.total = Decimal(str(total))
        order.amount = Decimal(str(total))  # Legacy field
        order.currency = Config.DEFAULT_CURRENCY or "NGN"
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
        
        # Step 7: Initialize payment via gateway
        payment_manager = PaymentManager()
        extra_meta = {
            "order_id": str(order.id),
            "order_number": order.order_number,
            "guest_email": request.email,
            "guest_token": request.guest_token,
            "guest_phone": request.phone,
            "guest_name": f"{(request.first_name or '').strip()} {(request.last_name or '').strip()}".strip(),
            "currency": order.currency,
        }
        payment_response = payment_manager.initialize_gateway_payment(
            amount=Decimal(str(total)),
            currency=order.currency,
            user=current_user,
            payment_type=PaymentType.ORDER_PAYMENT,
            narration=f"Payment for order {order.order_number}",
            extra_meta=extra_meta,
        )
        
        # Persist reference on order
        order.payment_ref = payment_response.get("reference")
        db.session.commit()
        
        log_event(f"Checkout initialized: Order {order.order_number}, Total: {total}")
        
        # Step 8: Send order confirmation email
        recipient_email = current_user.email if current_user else request.email
        if recipient_email:
            try:
                from ..emailing import email_service
                email_service.send_order_confirmation(
                    to=recipient_email,
                    order=order,
                    items=items_to_order,
                )
            except Exception as email_err:
                log_error("Failed to send order confirmation email", error=email_err)
                # Don't fail checkout if email fails
        
        
        result = CheckoutResult(
            success=True,
            order_id=str(order.id),
            payment_status=payment_response.get("status") or "pending_payment",
            authorization_url=payment_response.get("authorization_url"),
            payment_reference=payment_response.get("reference"),
        )
        
        # Store result in cache for idempotency (24 hour TTL)
        if request.idempotency_key:
            from ...extensions import app_cache
            cache_key = f"checkout:idempotency:{request.idempotency_key}"
            app_cache.set(cache_key, {
                "success": result.success,
                "order_id": result.order_id,
                "payment_status": result.payment_status,
                "authorization_url": result.authorization_url,
                "payment_reference": result.payment_reference,
            }, timeout=86400)  # 24 hours
        
        return result
        
    except IntegrityError as e:
        db.session.rollback()
        log_error("Database integrity error during checkout", error=e)
        return CheckoutResult(success=False, error="Checkout failed due to database error")
    except Exception as e:
        db.session.rollback()
        log_error("Checkout processing failed", error=e)
        return CheckoutResult(success=False, error=f"Checkout failed: {str(e)}")

