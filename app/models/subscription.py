from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Query, Mapped as M  # type: ignore
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..extensions import db
from ..utils.date_time import DateTimeUtils, timedelta

if TYPE_CHECKING:
    from .user import AppUser
    from .payment import Payment

class SubscriptionPlan(db.Model):
    """
    Model representing available subscription plans.
    """
    __tablename__ = "subscription_plan"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(14, 2), nullable=False)
    duration_days = db.Column(db.Integer(), nullable=False)
    features = db.Column(db.JSON, default=list)
    is_active = db.Column(db.Boolean(), default=True)
    
    created_at = db.Column(db.DateTime(timezone=True), default=DateTimeUtils.aware_utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=DateTimeUtils.aware_utcnow, onupdate=DateTimeUtils.aware_utcnow)
    
    def update(self, commit=True, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if commit:
            db.session.commit()

    def delete(self, commit=True):
        db.session.delete(self)
        if commit:
            db.session.commit()

class Subscription(db.Model):
    """
    Model representing a user's subscription.
    """
    __tablename__ = "subscription"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    start_date = db.Column(db.DateTime(timezone=True), nullable=False, default=DateTimeUtils.aware_utcnow)
    end_date = db.Column(db.DateTime(timezone=True), nullable=False)
    is_active = db.Column(db.Boolean(), default=True)
    auto_renew = db.Column(db.Boolean(), default=False)
    meta_info = db.Column(db.JSON, default=dict)
    
    created_at = db.Column(db.DateTime(timezone=True), default=DateTimeUtils.aware_utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=DateTimeUtils.aware_utcnow, onupdate=DateTimeUtils.aware_utcnow)

    # Relationships
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('app_user.id'), nullable=False)
    app_user= db.relationship('AppUser', back_populates='subscriptions')
    plan_id = db.Column(UUID(as_uuid=True), db.ForeignKey('subscription_plan.id'), nullable=False)
    plan= db.relationship('SubscriptionPlan')
    payment = db.relationship('Payment', back_populates='subscription', uselist=False)

    def extend_validity(self):
        """Extend subscription based on plan duration."""
        if self.end_date < DateTimeUtils.aware_utcnow():
            self.start_date = DateTimeUtils.aware_utcnow()
        self.end_date = self.end_date + timedelta(days=self.plan.duration_days)
        self.is_active = True
        db.session.commit()

    @property
    def is_expired(self) -> bool:
        """Check if subscription has expired."""
        return self.end_date < DateTimeUtils.aware_utcnow()
    
    def update(self, commit=True, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if commit:
            db.session.commit()

    def delete(self, commit=True):
        db.session.delete(self)
        if commit:
            db.session.commit()