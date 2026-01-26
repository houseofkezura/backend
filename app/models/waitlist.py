"""
Waitlist entry model.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Mapped as M
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..extensions import db
from quas_utils.date_time import QuasDateTime, to_gmt1_or_none
from ..enums.waitlist import WaitlistStatus


class WaitlistEntry(db.Model):
    """
    Waitlist entry model for pre-launch signups.
    """
    __tablename__ = "waitlist_entry"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email: M[str] = db.Column(db.String(255), nullable=False, unique=True, index=True)
    status: M[str] = db.Column(db.String(50), nullable=False, default=str(WaitlistStatus.PENDING), index=True)
    invited_at: M[Optional[datetime]] = db.Column(db.DateTime(timezone=True), nullable=True)
    converted_at: M[Optional[datetime]] = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, index=True)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)
    
    def __repr__(self) -> str:
        return f"<WaitlistEntry {self.id}, Email: {self.email}, Status: {self.status}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert waitlist entry to dictionary."""
        return {
            "id": str(self.id),
            "email": self.email,
            "status": self.status,
            "invited_at": to_gmt1_or_none(self.invited_at),
            "converted_at": to_gmt1_or_none(self.converted_at),
            "created_at": to_gmt1_or_none(self.created_at),
            "updated_at": to_gmt1_or_none(self.updated_at),
        }
