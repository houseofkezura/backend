"""
Audit logging model for tracking admin actions and financial events.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Mapped as M
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid

from ..extensions import db
from quas_utils.date_time import QuasDateTime, to_gmt1_or_none


class AuditLog(db.Model):
    """
    Audit log model for tracking important system events.
    """
    __tablename__ = "audit_log"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: M[Optional[uuid.UUID]] = db.Column(UUID(as_uuid=True), db.ForeignKey('app_user.id', ondelete='SET NULL'), nullable=True, index=True)
    action: M[str] = db.Column(db.String(100), nullable=False, index=True)  # e.g., "inventory_adjust", "loyalty_adjust", "payment_refund"
    resource_type: M[Optional[str]] = db.Column(db.String(50), nullable=True, index=True)  # e.g., "inventory", "loyalty", "payment"
    resource_id: M[Optional[uuid.UUID]] = db.Column(UUID(as_uuid=True), nullable=True, index=True)
    meta: M[Dict[str, Any]] = db.Column(JSON, default=dict)  # Additional metadata
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, index=True)
    
    # Relationships
    user = db.relationship('AppUser', backref='audit_logs')
    
    def __repr__(self) -> str:
        return f"<AuditLog {self.id}, Action: {self.action}, User: {self.user_id}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": str(self.resource_id) if self.resource_id else None,
            "meta": self.meta or {},
            "created_at": to_gmt1_or_none(self.created_at),
        }
    
    @classmethod
    def log_action(
        cls,
        action: str,
        user_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[uuid.UUID] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> "AuditLog":
        """
        Create an audit log entry.
        
        Args:
            action: Action name (e.g., "inventory_adjust")
            user_id: User who performed the action
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            meta: Additional metadata
            
        Returns:
            Created AuditLog instance
        """
        log_entry = cls()
        log_entry.action = action
        log_entry.user_id = user_id
        log_entry.resource_type = resource_type
        log_entry.resource_id = resource_id
        log_entry.meta = meta or {}
        
        db.session.add(log_entry)
        db.session.commit()
        
        return log_entry




