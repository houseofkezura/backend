"""
Wishlist model for saving favorite products.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Mapped as M, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..extensions import db
from quas_utils.date_time import QuasDateTime, to_gmt1_or_none

if TYPE_CHECKING:
    from .user import AppUser
    from .product import ProductVariant


class WishlistItem(db.Model):
    """
    WishlistItem model representing a saved product variant.
    
    Wishlist is authenticated-only (no guest support).
    Each user can save a variant only once.
    """
    __tablename__ = "wishlist_item"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey("product_variant.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, index=True)
    
    # Relationships
    user = relationship("AppUser", backref="wishlist_items")
    variant = relationship("ProductVariant")
    
    # Unique constraint: one variant per user
    __table_args__ = (
        db.UniqueConstraint('user_id', 'variant_id', name='uq_wishlist_user_variant'),
    )
    
    def __repr__(self) -> str:
        return f"<WishlistItem {self.id}, User: {self.user_id}, Variant: {self.variant_id}>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert wishlist item to dictionary."""
        variant_data = None
        if self.variant:
            variant_data = {
                "id": str(self.variant.id),
                "sku": self.variant.sku,
                "product_id": str(self.variant.product_id),
                "price_ngn": float(self.variant.price_ngn),
                "price_usd": float(self.variant.price_usd) if self.variant.price_usd else None,
                "attributes": self.variant.attributes or {},
                "is_in_stock": self.variant.is_in_stock,
                "product": {
                    "id": str(self.variant.product.id),
                    "name": self.variant.product.name,
                    "slug": self.variant.product.slug,
                } if self.variant.product else None,
            }
        
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "variant_id": str(self.variant_id),
            "variant": variant_data,
            "created_at": to_gmt1_or_none(self.created_at),
        }

