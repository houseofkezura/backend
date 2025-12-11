"""
CMS and B2B inquiry models.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Mapped as M
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..extensions import db
from quas_utils.date_time import QuasDateTime, to_gmt1_or_none


class CmsPage(db.Model):
    """
    CMS page model for static content.
    """
    __tablename__ = "cms_page"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    slug: M[str] = db.Column(db.String(255), nullable=False, unique=True, index=True)
    title: M[str] = db.Column(db.String(255), nullable=False)
    content: M[str] = db.Column(db.Text, nullable=False)
    published: M[bool] = db.Column(db.Boolean, nullable=False, default=False)
    published_at: M[Optional[datetime]] = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)
    
    def __repr__(self) -> str:
        return f"<CmsPage {self.id}, Slug: {self.slug}, Title: {self.title}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert CMS page to dictionary."""
        return {
            "id": str(self.id),
            "slug": self.slug,
            "title": self.title,
            "content": self.content,
            "published": self.published,
            "published_at": to_gmt1_or_none(self.published_at),
            "created_at": to_gmt1_or_none(self.created_at),
            "updated_at": to_gmt1_or_none(self.updated_at),
        }


class B2BInquiry(db.Model):
    """
    B2B wholesale inquiry model.
    """
    __tablename__ = "b2b_inquiry"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    business_name: M[str] = db.Column(db.String(255), nullable=False)
    business_type: M[Optional[str]] = db.Column(db.String(100), nullable=True)
    contact_name: M[str] = db.Column(db.String(255), nullable=False)
    email: M[str] = db.Column(db.String(255), nullable=False, index=True)
    phone: M[str] = db.Column(db.String(120), nullable=False)
    country: M[str] = db.Column(db.String(100), nullable=False)
    expected_volume: M[Optional[str]] = db.Column(db.String(100), nullable=True)
    product_categories: M[Optional[str]] = db.Column(db.Text, nullable=True)  # JSON array as string
    note: M[Optional[str]] = db.Column(db.Text, nullable=True)
    status: M[str] = db.Column(db.String(50), nullable=False, default="new")  # new, contacted, in_negotiation, closed
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, index=True)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)
    
    def __repr__(self) -> str:
        return f"<B2BInquiry {self.id}, Business: {self.business_name}, Status: {self.status}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert B2B inquiry to dictionary."""
        return {
            "id": str(self.id),
            "business_name": self.business_name,
            "business_type": self.business_type,
            "contact_name": self.contact_name,
            "email": self.email,
            "phone": self.phone,
            "country": self.country,
            "expected_volume": self.expected_volume,
            "product_categories": self.product_categories,
            "note": self.note,
            "status": self.status,
            "created_at": to_gmt1_or_none(self.created_at),
            "updated_at": to_gmt1_or_none(self.updated_at),
        }




