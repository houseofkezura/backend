"""
Base model with common functionality.
"""
from datetime import datetime
from flask_sqlalchemy import Model
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import Mapped as M, DynamicMapped as DM  # type: ignore
from sqlalchemy.dialects.postgresql import UUID
import uuid

from quas_utils.date_time import QuasDateTime, to_gmt1_or_none
from ..extensions import db


class BaseModel(Model):
    """Base model with common fields and methods."""
    
    __abstract__ = True
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    created_at = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)
    
    def save(self):
        """Save the model instance."""
        from app.extensions import db
        db.session.add(self)
        db.session.commit()
        return self
    
    def update(self, commit=True, **kwargs) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)
        
        if commit:
            db.session.commit()
    
    def delete(self):
        """Delete the model instance."""
        from app.extensions import db
        db.session.delete(self)
        db.session.commit()
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}