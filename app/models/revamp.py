"""
Revamp request model for wig revamp tracking.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Mapped as M, relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid

from ..extensions import db
from quas_utils.date_time import QuasDateTime, to_gmt1_or_none

if TYPE_CHECKING:
    from .user import AppUser
    from .order import OrderItem


class RevampRequest(db.Model):
    """
    Revamp request model for tracking wig revamp requests.
    """
    __tablename__ = "revamp_request"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey('app_user.id', ondelete='CASCADE'), nullable=False, index=True)
    order_item_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey('order_item.id', ondelete='CASCADE'), nullable=False, index=True)
    description: M[str] = db.Column(db.Text, nullable=False)
    images: M[List[str]] = db.Column(db.JSON, default=list)  # List of media IDs
    status: M[str] = db.Column(db.String(50), nullable=False, default="pending", index=True)  # pending, in_progress, completed, cancelled
    assigned_to: M[Optional[uuid.UUID]] = db.Column(UUID(as_uuid=True), db.ForeignKey('crm_staff.id'), nullable=True)
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, index=True)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)
    
    # Relationships
    user = relationship('AppUser', backref='revamp_requests')
    order_item = relationship('OrderItem', backref='revamp_requests')
    assigned_staff = relationship('CrmStaff', backref='assigned_revamps')
    
    def __repr__(self) -> str:
        return f"<RevampRequest {self.id}, User: {self.user_id}, Status: {self.status}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert revamp request to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "order_item_id": str(self.order_item_id),
            "description": self.description,
            "images": self.images or [],
            "status": self.status,
            "assigned_to": str(self.assigned_to) if self.assigned_to else None,
            "created_at": to_gmt1_or_none(self.created_at),
            "updated_at": to_gmt1_or_none(self.updated_at),
        }

