from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Dict, Any
from datetime import datetime
import secrets
import string

from sqlalchemy.orm import Mapped as M, relationship  # type: ignore
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid

from ..extensions import db
from quas_utils.date_time import QuasDateTime, to_gmt1_or_none
from ..enums.orders import OrderStatus

if TYPE_CHECKING:
    from .user import AppUser


class Order(db.Model):
    """
    E-commerce order model.
    Supports both authenticated users and guest orders.
    """
    __tablename__ = "order"

    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: M[Optional[uuid.UUID]] = db.Column(UUID(as_uuid=True), db.ForeignKey('app_user.id'), nullable=True, index=True)
    
    # Human-readable order number (e.g., KEZ-A7B3C9D2)
    order_number: M[str] = db.Column(db.String(12), unique=True, nullable=False, index=True)
    
    # Order status
    status: M[str] = db.Column(db.String(50), nullable=False, default=str(OrderStatus.PENDING), index=True)
    
    # Pricing breakdown
    subtotal: M[float] = db.Column(db.Numeric(14, 2), nullable=False)
    shipping_cost: M[float] = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    discount: M[float] = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    points_redeemed: M[int] = db.Column(db.Integer, nullable=False, default=0)
    total: M[float] = db.Column(db.Numeric(14, 2), nullable=False)
    
    # Legacy field for backward compatibility
    amount: M[float] = db.Column(db.Numeric(14, 2), nullable=False)
    
    # Currency
    currency: M[str] = db.Column(db.String(3), nullable=False, default="NGN")
    
    # Payment
    payment_ref: M[Optional[str]] = db.Column(db.String(255), nullable=True)
    payment_url: M[Optional[str]] = db.Column(db.Text, nullable=True)  # Store authorization_url for re-completing payment
    
    @staticmethod
    def generate_order_number(max_attempts: int = 10) -> str:
        """
        Generate a unique, human-readable order number.
        
        Format: KEZ-XXXXXXXX (8 uppercase alphanumeric characters after prefix).
        Uses cryptographically secure random generation and checks database
        for collisions, retrying up to max_attempts times.
        
        Args:
            max_attempts: Maximum number of generation attempts before raising an error.
        
        Returns:
            A unique order number string (e.g., 'KEZ-A7B3C9D2').
        
        Raises:
            RuntimeError: If unable to generate a unique number after max_attempts.
        """
        # Use only uppercase letters and digits, excluding ambiguous characters (0, O, I, L, 1)
        alphabet = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
        prefix = "KEZ-"
        
        for _ in range(max_attempts):
            random_part = ''.join(secrets.choice(alphabet) for _ in range(8))
            candidate = f"{prefix}{random_part}"
            
            # Check if this order number already exists
            existing = Order.query.filter_by(order_number=candidate).first()
            if existing is None:
                return candidate
        
        raise RuntimeError(
            f"Failed to generate unique order number after {max_attempts} attempts. "
            "This indicates an extremely unlikely collision scenario or database issue."
        )
    
    # Shipping address snapshot (stored as JSON for guest orders)
    shipping_address: M[Dict[str, Any]] = db.Column(JSON, nullable=True)
    
    # CRM staff tracking
    packed_by_crm_id: M[Optional[uuid.UUID]] = db.Column(UUID(as_uuid=True), db.ForeignKey('crm_staff.id'), nullable=True)
    
    # Guest order tracking
    guest_email: M[Optional[str]] = db.Column(db.String(255), nullable=True, index=True)
    guest_phone: M[Optional[str]] = db.Column(db.String(120), nullable=True)
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, index=True)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)

    # Relationships
    app_user = db.relationship('AppUser', back_populates='orders')
    items = relationship('OrderItem', back_populates='order', cascade='all, delete-orphan')
    shipments = relationship('Shipment', back_populates='order', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Order ID: {self.id}, Status: {self.status}, Total: {self.total}>'

    def update(self, commit=True, **kwargs):
        """Update order attributes."""
        for key, value in kwargs.items():
            setattr(self, key, value)
        if commit:
            db.session.commit()

    def delete(self, commit=True):
        """Delete the order."""
        db.session.delete(self)
        if commit:
            db.session.commit()

    def to_dict(self, user: bool = False, include_items: bool = False) -> dict:
        """
        Convert order to dictionary.
        
        Args:
            user: Whether to include full user info
            include_items: Whether to include order items
        """
        user_info = {'user': self.app_user.to_dict()} if user and self.app_user else {'user_id': str(self.user_id) if self.user_id else None}
        
        data = {
            'id': str(self.id),
            'order_number': self.order_number,
            'status': str(self.status),
            'subtotal': float(self.subtotal),
            'shipping_cost': float(self.shipping_cost),
            'discount': float(self.discount),
            'points_redeemed': self.points_redeemed,
            'total': float(self.total),
            'amount': float(self.amount),  # Legacy field
            'currency': self.currency,
            'payment_ref': self.payment_ref,
            'payment_url': self.payment_url,
            'shipping_address': self.shipping_address or {},
            'packed_by_crm_id': str(self.packed_by_crm_id) if self.packed_by_crm_id else None,
            'guest_email': self.guest_email,
            'guest_phone': self.guest_phone,
            'created_at': to_gmt1_or_none(self.created_at),
            'updated_at': to_gmt1_or_none(self.updated_at),
            **user_info,
        }
        
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
        
        return data


class OrderItem(db.Model):
    """
    Order item model representing a line item in an order.
    """
    __tablename__ = "order_item"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    order_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey('order.id', ondelete='CASCADE'), nullable=False, index=True)
    variant_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey('product_variant.id'), nullable=False, index=True)
    quantity: M[int] = db.Column(db.Integer, nullable=False)
    unit_price: M[float] = db.Column(db.Numeric(14, 2), nullable=False)  # Snapshot of price at order time
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow)
    
    # Relationships
    order = relationship('Order', back_populates='items')
    variant = relationship('ProductVariant')
    
    def __repr__(self):
        return f'<OrderItem {self.id}, Order: {self.order_id}, Variant: {self.variant_id}, Qty: {self.quantity}>'
    
    @property
    def line_total(self) -> float:
        """Calculate line item total."""
        return self.quantity * float(self.unit_price)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert order item to dictionary."""
        variant_data = None
        if self.variant:
            variant_data = {
                "id": str(self.variant.id),
                "sku": self.variant.sku,
                "product_id": str(self.variant.product_id),
                "attributes": self.variant.attributes or {},
            }
        
        return {
            "id": str(self.id),
            "order_id": str(self.order_id),
            "variant_id": str(self.variant_id),
            "variant": variant_data,
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "line_total": self.line_total,
            "created_at": to_gmt1_or_none(self.created_at),
        }


class Shipment(db.Model):
    """
    Shipment model for tracking order shipments.
    """
    __tablename__ = "shipment"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    order_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey('order.id', ondelete='CASCADE'), nullable=False, index=True)
    courier: M[Optional[str]] = db.Column(db.String(100), nullable=True)
    tracking_number: M[Optional[str]] = db.Column(db.String(255), nullable=True, index=True)
    status: M[str] = db.Column(db.String(50), nullable=False, default="pending")
    estimated_delivery: M[Optional[datetime]] = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)
    
    # Relationships
    order = relationship('Order', back_populates='shipments')
    
    def __repr__(self):
        return f'<Shipment {self.id}, Order: {self.order_id}, Tracking: {self.tracking_number}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert shipment to dictionary."""
        return {
            "id": str(self.id),
            "order_id": str(self.order_id),
            "courier": self.courier,
            "tracking_number": self.tracking_number,
            "status": self.status,
            "estimated_delivery": to_gmt1_or_none(self.estimated_delivery),
            "created_at": to_gmt1_or_none(self.created_at),
            "updated_at": to_gmt1_or_none(self.updated_at),
        }


