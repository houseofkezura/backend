
from enum import Enum

from ..extensions import db
from ..utils.helpers.basics import generate_random_string
from ..utils.date_time import DateTimeUtils
from ..enums.settings import GeneralSettingsKeys, PaymentMethodSettingKeys



class GeneralSetting(db.Model):
    """
    Database model for storing key-value general settings.

    Attributes:
        key (str): The unique identifier for the setting.
        value (str): The stored value for the setting.
    """
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=DateTimeUtils.aware_utcnow, onupdate=DateTimeUtils.aware_utcnow)


    def __repr__(self):
        return f'<GeneralSetting key: {self.key}, value: {self.value}>'
    
    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self, commit=True, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if commit:
            db.session.commit()

    def delete(self, commit=True):
        db.session.delete(self)
        if commit:
            db.session.commit()
    
    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value,
            'updated_at': self.updated_at
        }


class PaymentMethodSettings(db.Model):
    """
    Stores settings for each payment method using a key-value structure.
    """
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String(50), nullable=False)  # e.g., 'bacs', 'cod', 'gateway'
    key = db.Column(db.String(100), nullable=False)  # e.g., 'enabled', 'account_number'
    value = db.Column(db.Text, nullable=True)  # Store values like True/False, text, API keys
    updated_at = db.Column(db.DateTime(timezone=True), default=DateTimeUtils.aware_utcnow, onupdate=DateTimeUtils.aware_utcnow)
    
    __table_args__ = (db.UniqueConstraint('method', 'key', name='uq_method_key'),)
    
    def __repr__(self):
        return f'<PaymentMethodSettings method: {self.method}, key: {self.key}, value: {self.value}>'
    
    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'method': self.method,
            'key': self.key,
            'value': self.value,
            'updated_at': self.updated_at
        }