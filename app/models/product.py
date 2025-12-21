"""
Product, ProductVariant, and Inventory models for the e-commerce catalog.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Dict, Any, cast
from datetime import datetime
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Query, Mapped as M, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSON
import uuid

from ..extensions import db
from quas_utils.date_time import QuasDateTime, to_gmt1_or_none
from ..enums.products import (
    ProductCategory,
    HairType,
    Texture,
    LaceType,
    Density,
    CapSize,
    LaunchStatus,
)

if TYPE_CHECKING:
    from .media import Media
    from .inventory import Inventory


class Product(db.Model):
    """
    Product model representing a base product (e.g., a wig style).
    Products have variants (different lengths, colors, etc.).
    """
    __tablename__ = "product"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: M[str] = db.Column(db.String(255), nullable=False)
    sku: M[str] = db.Column(db.String(100), nullable=False, unique=True, index=True)  # Product SKU
    slug: M[str] = db.Column(db.String(255), nullable=False, unique=True, index=True)
    description: M[Optional[str]] = db.Column(db.Text)
    category: M[str] = db.Column(db.String(50), nullable=False)  # ProductCategory enum value
    product_metadata: M[Dict[str, Any]] = db.Column(JSON, default=dict, name="metadata")  # SEO, tags, etc. (stored as 'metadata' in DB)
    
    # Product details
    care: M[Optional[str]] = db.Column(db.Text)  # Product care instructions
    details: M[Optional[str]] = db.Column(db.Text)  # Product details
    material: M[Optional[str]] = db.Column(db.String(255))  # Product material
    
    # SEO fields
    meta_title: M[Optional[str]] = db.Column(db.String(255))
    meta_description: M[Optional[str]] = db.Column(db.Text)
    meta_keywords: M[Optional[str]] = db.Column(db.String(500))
    
    # Launch status (default: "In-Stock")
    launch_status: M[str] = db.Column(db.String(50), default="In-Stock")
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, index=True)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)
    
    # Relationships
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Product {self.id}, {self.name}>"
    
    @staticmethod
    def add_search_filters(query: Query, search_term: str) -> Query:
        """Add search filters to a query."""
        if search_term:
            search_term = f"%{search_term}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.sku.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.slug.ilike(search_term),
                )
            )
        return query
    
    def to_dict(self, include_variants: bool = False) -> Dict[str, Any]:
        """Convert product to dictionary."""
        data = {
            "id": str(self.id),
            "name": self.name,
            "sku": self.sku,
            "slug": self.slug,
            "description": self.description or "",
            "category": self.category,
            "care": self.care or "",
            "details": self.details or "",
            "material": self.material or "",
            "metadata": self.product_metadata or {},
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "meta_keywords": self.meta_keywords,
            "status": self.launch_status,  # Alias for launch_status
            "launch_status": self.launch_status,
            "created_at": to_gmt1_or_none(self.created_at),
            "updated_at": to_gmt1_or_none(self.updated_at),
        }
        
        if include_variants:
            data["variants"] = [v.to_dict() for v in self.variants]
        
        return data


class ProductVariant(db.Model):
    """
    Product variant model representing a specific SKU (e.g., 32" straight, black).
    """
    __tablename__ = "product_variant"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    product_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey("product.id", ondelete="CASCADE"), nullable=False, index=True)
    sku: M[str] = db.Column(db.String(100), nullable=False, unique=True, index=True)
    
    # Pricing
    price_ngn: M[float] = db.Column(db.Numeric(14, 2), nullable=False)
    price_usd: M[Optional[float]] = db.Column(db.Numeric(14, 2))
    
    # Physical attributes
    weight_g: M[Optional[int]] = db.Column(db.Integer)  # Weight in grams
    
    # Product attributes stored as JSON
    # Contains: length, texture, color, lace_type, density, cap_size, hair_type
    attributes: M[Dict[str, Any]] = db.Column(JSON, default=dict)
    
    # Relationships
    product = relationship("Product", back_populates="variants")
    inventory = relationship("Inventory", back_populates="variant", uselist=False, cascade="all, delete-orphan")
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)
    
    def __repr__(self) -> str:
        return f"<ProductVariant {self.id}, SKU: {self.sku}>"
    
    @property
    def is_in_stock(self) -> bool:
        """Check if variant is in stock."""
        if self.inventory:
            return self.inventory.quantity > 0
        return False
    
    @property
    def stock_quantity(self) -> int:
        """Get current stock quantity."""
        if self.inventory:
            return self.inventory.quantity
        return 0
    
    def to_dict(self, include_inventory: bool = False) -> Dict[str, Any]:
        """Convert variant to dictionary."""
        data = {
            "id": str(self.id),
            "product_id": str(self.product_id),
            "sku": self.sku,
            "price_ngn": float(self.price_ngn),
            "price_usd": float(self.price_usd) if self.price_usd else None,
            "weight_g": self.weight_g,
            "attributes": self.attributes or {},
            "is_in_stock": self.is_in_stock,
            "created_at": to_gmt1_or_none(self.created_at),
            "updated_at": to_gmt1_or_none(self.updated_at),
        }
        
        if include_inventory and self.inventory:
            data["inventory"] = self.inventory.to_dict()
        
        return data


# Association table for variant-media many-to-many relationship
variant_media = db.Table(
    "variant_media",
    db.Column("variant_id", UUID(as_uuid=True), db.ForeignKey("product_variant.id", ondelete="CASCADE"), primary_key=True),
    db.Column("media_id", UUID(as_uuid=True), db.ForeignKey("media.id", ondelete="CASCADE"), primary_key=True),
)


class Inventory(db.Model):
    """
    Inventory model tracking stock levels per variant.
    """
    __tablename__ = "inventory"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    variant_id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), db.ForeignKey("product_variant.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    quantity: M[int] = db.Column(db.Integer, nullable=False, default=0)
    low_stock_threshold: M[int] = db.Column(db.Integer, nullable=False, default=5)
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)
    
    # Relationships
    variant = relationship("ProductVariant", back_populates="inventory")
    
    def __repr__(self) -> str:
        return f"<Inventory {self.id}, Variant: {self.variant_id}, Qty: {self.quantity}>"
    
    @property
    def is_low_stock(self) -> bool:
        """Check if inventory is below low stock threshold."""
        return self.quantity <= self.low_stock_threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert inventory to dictionary."""
        return {
            "id": str(self.id),
            "variant_id": str(self.variant_id),
            "quantity": self.quantity,
            "low_stock_threshold": self.low_stock_threshold,
            "is_low_stock": self.is_low_stock,
            "created_at": to_gmt1_or_none(self.created_at),
            "updated_at": to_gmt1_or_none(self.updated_at),
        }

