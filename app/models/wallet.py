"""
Author: Emmanuel Olowu
Link: https://github.com/zeddyemy
Copyright: © 2024 Emmanuel Olowu <zeddyemy@gmail.com>
License: GNU, see LICENSE for more details.
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import or_
from sqlalchemy.orm import backref, Mapped as M  # type: ignore
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..extensions import db
from config import Config
from quas_utils.date_time import QuasDateTime

if TYPE_CHECKING:
    from .user import AppUser

class Wallet(db.Model):
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    _balance = db.Column(db.Numeric(14, 2), default=0.00, nullable=True)
    currency_name = db.Column(db.String(50), default='Naira', nullable=True)
    currency_code = db.Column(db.String(10), default='NGN', nullable=True)
    currency_symbol = db.Column(db.String(10), default=str('₦'), nullable=True)
    date_created = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('app_user.id', ondelete='CASCADE'), nullable=False,)
    
    app_user = db.relationship('AppUser', back_populates="wallet")
    
    @property
    def balance(self):
        return self._balance

    @balance.setter
    def balance(self, value):
        if isinstance(value, (int, float)):
            value = round(value, 2)
        elif isinstance(value, str):
            value = round(float(value), 2)
        self._balance = value
    
    def __repr__(self):
        return f'<Wallet ID: {self.id}, balance: {self.balance}>'
    
    def update(self, commit=True, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if commit:
            db.session.commit()

    def delete(self, commit=True):
        db.session.delete(self)
        if commit:
            db.session.commit()
    
    def to_dict(self, user=False):
        user_info = {'user': self.app_user.to_dict(),} if user else {'user_id': self.user_id} # optionally include user info in dict
        
        return {
            'id': self.id,
            'balance': self.balance,
            'currency_name': self.currency_name,
            'currency_code': self.currency_code,
            'currency_symbol': self.currency_symbol,
            **user_info,
        }