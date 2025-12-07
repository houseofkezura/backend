"""
Loyalty program models for House of Kezura Club.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped as M, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..extensions import db
from ..utils.date_time import DateTimeUtils, to_gmt1_or_none

if TYPE_CHECKING:
    from .user import AppUser
    from .order import Order


# Loyalty tier constants
LOYALTY_TIER_MUSE = "Muse"
LOYALTY_TIER_ICON = "Icon"
LOYALTY_TIER_EMPRESS = "Empress"

# Loyalty ledger entry types
LEDGER_TYPE_EARN = "earn"
LEDGER_TYPE_REDEEM = "redeem"
LEDGER_TYPE_ADJUST = "adjust"
LEDGER_TYPE_EXPIRE = "expire"


class LoyaltyAccount(db.Model):
    """
    Loyalty account model for House of Kezura Club.
    """
    __tablename__ = "loyalty_account"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey('app_user.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    tier: M[str] = db.Column(db.String(50), nullable=False, default=LOYALTY_TIER_MUSE)
    points_balance: M[int] = db.Column(db.Integer, nullable=False, default=0)
    lifetime_spend: M[float] = db.Column(db.Numeric(14, 2), nullable=False, default=0)
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=DateTimeUtils.aware_utcnow)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=DateTimeUtils.aware_utcnow, onupdate=DateTimeUtils.aware_utcnow)
    
    # Relationships
    user = relationship('AppUser', backref='loyalty_account')
    ledger_entries = relationship('LoyaltyLedger', back_populates='account', cascade='all, delete-orphan')
    
    def __repr__(self) -> str:
        return f"<LoyaltyAccount {self.id}, User: {self.user_id}, Tier: {self.tier}, Points: {self.points_balance}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert loyalty account to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "tier": self.tier,
            "points_balance": self.points_balance,
            "lifetime_spend": float(self.lifetime_spend),
            "created_at": to_gmt1_or_none(self.created_at),
            "updated_at": to_gmt1_or_none(self.updated_at),
        }


class LoyaltyLedger(db.Model):
    """
    Loyalty ledger model for tracking points transactions.
    """
    __tablename__ = "loyalty_ledger"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    account_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey('loyalty_account.id', ondelete='CASCADE'), nullable=False, index=True)
    type: M[str] = db.Column(db.String(50), nullable=False, index=True)  # earn, redeem, adjust, expire
    points: M[int] = db.Column(db.Integer, nullable=False)  # Positive for earn, negative for redeem
    reason: M[Optional[str]] = db.Column(db.String(255), nullable=True)
    ref_id: M[Optional[uuid.UUID]] = db.Column(UUID(as_uuid=True), nullable=True, index=True)  # Order ID, campaign ID, etc.
    ref_type: M[Optional[str]] = db.Column(db.String(50), nullable=True)  # order, campaign, manual, etc.
    
    # Expiry tracking
    expires_at: M[Optional[datetime]] = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=DateTimeUtils.aware_utcnow, index=True)
    
    # Relationships
    account = relationship('LoyaltyAccount', back_populates='ledger_entries')
    
    def __repr__(self) -> str:
        return f"<LoyaltyLedger {self.id}, Account: {self.account_id}, Type: {self.type}, Points: {self.points}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert ledger entry to dictionary."""
        return {
            "id": str(self.id),
            "account_id": str(self.account_id),
            "type": self.type,
            "points": self.points,
            "reason": self.reason,
            "ref_id": str(self.ref_id) if self.ref_id else None,
            "ref_type": self.ref_type,
            "expires_at": to_gmt1_or_none(self.expires_at),
            "created_at": to_gmt1_or_none(self.created_at),
        }

