"""
Cart and CartItem models for shopping cart functionality.
Supports both authenticated users and guest carts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Mapped as M, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..extensions import db
from quas_utils.date_time import QuasDateTime, to_gmt1_or_none

if TYPE_CHECKING:
    from .user import AppUser
    from .product import ProductVariant


class Cart(db.Model):
    """
    Cart model for storing shopping carts.
    
    For authenticated users: linked to AppUser via user_id.
    For guests: user_id is None, identified by guest_token.
    """
    __tablename__ = "cart"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: M[Optional[uuid.UUID]] = db.Column(UUID(as_uuid=True), db.ForeignKey("app_user.id", ondelete="CASCADE"), nullable=True, index=True)
    guest_token: M[Optional[str]] = db.Column(db.String(255), nullable=True, unique=True, index=True)
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, index=True)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)
    
    # Relationships
    user = relationship("AppUser", backref="carts")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Cart {self.id}, User: {self.user_id}, Guest: {self.guest_token}>"
    
    @property
    def total_items(self) -> int:
        """Get total number of items in cart."""
        return sum(item.quantity for item in self.items)
    
    @property
    def subtotal(self) -> float:
        """Calculate cart subtotal."""
        return sum(item.quantity * float(item.unit_price) for item in self.items)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cart to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "guest_token": self.guest_token,
            "items": [item.to_dict() for item in self.items],
            "total_items": self.total_items,
            "subtotal": self.subtotal,
            "created_at": to_gmt1_or_none(self.created_at),
            "updated_at": to_gmt1_or_none(self.updated_at),
        }


class CartItem(db.Model):
    """
    CartItem model representing a line item in a cart.
    """
    __tablename__ = "cart_item"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    cart_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey("cart.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey("product_variant.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity: M[int] = db.Column(db.Integer, nullable=False, default=1)
    unit_price: M[float] = db.Column(db.Numeric(14, 2), nullable=False)  # Snapshot of price at add time
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)
    
    # Relationships
    cart = relationship("Cart", back_populates="items")
    variant = relationship("ProductVariant")
    
    def __repr__(self) -> str:
        return f"<CartItem {self.id}, Cart: {self.cart_id}, Variant: {self.variant_id}, Qty: {self.quantity}>"
    
    @property
    def line_total(self) -> float:
        """Calculate line item total."""
        return self.quantity * float(self.unit_price)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cart item to dictionary."""
        variant_data = None
        if self.variant:
            # Get variant data with images and product info
            variant_dict = self.variant.to_dict(include_inventory=True, include_product_info=True)
            variant_data = variant_dict
        
        return {
            "id": str(self.id),
            "cart_id": str(self.cart_id),
            "variant_id": str(self.variant_id),
            "variant": variant_data,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "line_total": self.line_total,
            "created_at": to_gmt1_or_none(self.created_at),
            "updated_at": to_gmt1_or_none(self.updated_at),
        }

