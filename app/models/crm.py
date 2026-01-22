"""
CRM staff and rating models.
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
    from .order import Order


class CrmStaff(db.Model):
    """
    CRM staff model for tracking packaging and customer service staff.
    """
    __tablename__ = "crm_staff"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: M[str] = db.Column(db.String(255), nullable=False)
    staff_code: M[str] = db.Column(db.String(50), nullable=False, unique=True, index=True)
    contact: M[Optional[str]] = db.Column(db.String(255), nullable=True)
    role: M[Optional[str]] = db.Column(db.String(100), nullable=True)
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)
    
    # Relationships
    packed_orders = relationship('Order', backref='packed_by_staff', foreign_keys='Order.packed_by_crm_id')
    ratings = relationship('CrmRating', back_populates='crm_staff')
    
    def __repr__(self) -> str:
        return f"<CrmStaff {self.id}, Code: {self.staff_code}, Name: {self.name}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert CRM staff to dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "staff_code": self.staff_code,
            "contact": self.contact,
            "role": self.role,
            "created_at": to_gmt1_or_none(self.created_at),
            "updated_at": to_gmt1_or_none(self.updated_at),
        }


class CrmRating(db.Model):
    """
    CRM rating model for customer ratings of staff.
    """
    __tablename__ = "crm_rating"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    order_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey('order.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    crm_staff_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey('crm_staff.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id: M[Optional[uuid.UUID]] = db.Column(UUID(as_uuid=True), db.ForeignKey('app_user.id', ondelete='CASCADE'), nullable=True, index=True)
    stars: M[int] = db.Column(db.Integer, nullable=False)  # 1-5
    comment: M[Optional[str]] = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, index=True)
    
    # Relationships
    order = relationship('Order', backref='rating')
    crm_staff = relationship('CrmStaff', back_populates='ratings')
    user = relationship('AppUser', backref='crm_ratings')
    
    def __repr__(self) -> str:
        return f"<CrmRating {self.id}, Order: {self.order_id}, Stars: {self.stars}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rating to dictionary."""
        return {
            "id": str(self.id),
            "order_id": str(self.order_id),
            "crm_staff_id": str(self.crm_staff_id),
            "user_id": str(self.user_id) if self.user_id else None,
            "stars": self.stars,
            "comment": self.comment,
            "created_at": to_gmt1_or_none(self.created_at),
        }








