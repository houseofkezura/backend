from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Mapped as M  # type: ignore
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..extensions import db
from ..utils.date_time import DateTimeUtils
from ..enums.orders import OrderStatus

if TYPE_CHECKING:
    from .user import AppUser


class Order(db.Model):
    """
    Model representing a general order on the platform.
    This model can be used for various types of orders, not just eSIM orders.
    """
    __tablename__ = "order"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('app_user.id'), nullable=False)
    status = db.Column(db.Enum(OrderStatus), nullable=False, default=OrderStatus.PENDING)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    payment_ref = db.Column(db.String(255), nullable=True)
    
    created_at = db.Column(db.DateTime(timezone=True), default=DateTimeUtils.aware_utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=DateTimeUtils.aware_utcnow, onupdate=DateTimeUtils.aware_utcnow)

    # Relationships
    app_user = db.relationship('AppUser', back_populates='orders')

    def __repr__(self):
        return f'<Order ID: {self.id}, Status: {self.status}, Amount: {self.amount}>'

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

    def to_dict(self, user: bool = False, esim_purchases: bool = False) -> dict:
        """
        Convert order to dictionary.
        
        Args:
            user: Whether to include full user info
            esim_purchases: Whether to include eSIM purchases
        """
        user_info = {'user': self.app_user.to_dict()} if user else {'user_id': self.user_id}
        
        return {
            'id': str(self.id),
            'status': str(self.status.value) if isinstance(self.status, OrderStatus) else str(self.status),
            'amount': float(self.amount),
            'payment_ref': self.payment_ref,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            **user_info,
        }


