from __future__ import annotations
from typing import TYPE_CHECKING, Optional

from enum import Enum
from sqlalchemy.orm import Query, Mapped as M  # type: ignore
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..extensions import db
from quas_utils.misc import generate_random_string
from quas_utils.date_time import QuasDateTime
from ..utils.payments.rates import convert_amount
from ..enums.payments import PaymentStatus, TransactionType

if TYPE_CHECKING:
    from .user import AppUser
    from .subscription import Subscription

class Payment(db.Model):
    """
    Model to represent a payment request made by a user in Folio Builder.
    This model captures details about a payment request before it is processed.
    """
    __tablename__ = "payment"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    key = db.Column(db.String(80), unique=True, nullable=False) # Unique identifier for the payments
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    narration = db.Column(db.String(255), nullable=True)
    payment_method = db.Column(db.String(80), nullable=False)  # 'wallet' or 'payment gateway(flutterwave)'
    status = db.Column(db.String(20), nullable=False, default=str(PaymentStatus.PENDING))  # Status of the payment request
    meta_info = db.Column(db.JSON, default=dict)  # Store payment type and related data
    
    created_at = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)

    # relationships
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('app_user.id'), nullable=True)
    app_user = db.relationship('AppUser', back_populates='payments')
    
    subscription_id = db.Column(UUID(as_uuid=True), db.ForeignKey('subscription.id'), nullable=True)
    subscription = db.relationship('Subscription', back_populates='payment')
    
    def __repr__(self):
        return f'<ID: {self.id}, Amount: {self.amount}, Payment Method: {self.payment_method}>'
    
    @property
    def currency_code(self):
        # Prefer user's wallet if available; otherwise fall back to meta_info or default
        if getattr(self, "app_user", None) and getattr(self.app_user, "wallet", None):
            return self.app_user.wallet.currency_code
        meta_currency = None
        try:
            meta_currency = (self.meta_info or {}).get("currency")
        except Exception:
            meta_currency = None
        return meta_currency or "NGN"
    
    @classmethod
    def create_payment_record(cls, key, amount, payment_method, status, app_user, commit=True, **kwargs):
        """Create and persist a new Payment record.

        Uses attribute assignment to satisfy static typing for SQLAlchemy models.
        """
        payment_record = cls()
        payment_record.key = key
        payment_record.amount = amount
        payment_record.payment_method = payment_method
        payment_record.status = str(status)
        payment_record.app_user = app_user
        
        # Set additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(payment_record, key, value)
        
        db.session.add(payment_record)
        
        if commit:
            db.session.commit()
        
        return payment_record
    
    def update(self, commit=True, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        if commit:
            db.session.commit()
    
    def delete(self, commit=True):
        db.session.delete(self)
        if commit:
            db.session.commit()
    
    def to_dict(self, user: bool = False) -> dict:
        user_info = {'user': self.app_user.to_dict()} if user else {'user_id': str(self.user_id)} # optionally include user info in dict
        return {
            'id': str(self.id),
            'key': self.key,
            'amount': convert_amount(self.amount, self.currency_code),
            'narration': self.narration,
            'payment_method': self.payment_method,
            'status': self.status,
            'meta_info': self.meta_info if self.meta_info else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            **user_info,
        }


class Transaction(db.Model):
    """
    Model to represent a financial transaction associated with a payment on the platform.
    This model captures details about the financial aspect of a payment or withdrawal.
    """
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    key = db.Column(db.String(80), unique=True, nullable=False) # Unique identifier for the financial transaction
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    transaction_type = db.Column(db.String(80), nullable=False) # 'credit', 'debit', 'payment' or 'withdraw'
    narration = db.Column(db.String(150), nullable=True)
    status = db.Column(db.String(80), nullable=False) # Status of the financial transaction
    meta_info = db.Column(db.JSON, default=dict)  # Store addition info or related data
    
    created_at = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)
    
    # Relationship with the user model
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('app_user.id'), nullable=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('app_user.id'), nullable=True)
    app_user = db.relationship('AppUser', backref=db.backref('transactions', lazy='dynamic'))
    
    @property
    def currency_code(self):
        if getattr(self, "app_user", None) and getattr(self.app_user, "wallet", None):
            return self.app_user.wallet.currency_code
        meta_currency = None
        try:
            meta_currency = (self.meta_info or {}).get("currency")
        except Exception:
            meta_currency = None
        return meta_currency or "NGN"
    
    def __repr__(self):
        return f'<ID: {self.id}, Transaction Reference: {self.key}, Transaction Type: {self.transaction_type}, Status: {self.status}>'
    
    
    @classmethod
    def create_transaction(cls, key, amount, transaction_type, narration, status, app_user, commit=True, **kwargs):
        """Create and persist a new Transaction record.

        Uses attribute assignment to satisfy static typing for SQLAlchemy models.
        """
        transaction = cls()
        transaction.key = key
        transaction.amount = amount
        transaction.transaction_type = str(transaction_type)
        transaction.narration = narration
        transaction.status = str(status)
        transaction.app_user = app_user
        
        # Set additional attributes from kwargs
        for key, value in kwargs.items():
            setattr(transaction, key, value)
        
        
        db.session.add(transaction)
        
        if commit:
            db.session.commit()
        
        return transaction
    
    def update(self, commit=True, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        if commit:
            db.session.commit()
    
    def delete(self, commit=True):
        db.session.delete(self)
        if commit:
            db.session.commit()
    
    def to_dict(self, user: bool = False) -> dict:
        user_info = {'user': self.app_user.to_dict(),} if user else {'user_id': self.user_id} # optionally include user info in dict
        return {
            'id': self.id,
            'key': self.key,
            'amount': convert_amount(self.amount, self.currency_code),
            'transaction_type': str(self.transaction_type),
            'narration': self.narration,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            **user_info,
        }

