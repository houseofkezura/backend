"""
Product, ProductVariant, ProductMaterial, and Inventory models for the e-commerce catalog.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Dict, Any, cast
from datetime import datetime
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Query, Mapped as M, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSON
import uuid

from app.extensions import db
from quas_utils.date_time import QuasDateTime, to_gmt1_or_none
from app.enums.products import (
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


# association table for the many-to-many relationship between products and categories
product_categories = db.Table("product_categories",
    db.Column("product_id", UUID(as_uuid=True), db.ForeignKey("product.id"), primary_key=True),
    db.Column("product_category_id", UUID(as_uuid=True), db.ForeignKey("product_category.id"), primary_key=True)
)


class ProductMaterial(db.Model):
    """
    ProductMaterial model representing materials that can be used for products.
    Admins can create materials and link them to products.
    """
    __tablename__ = "product_material"
    
    id: M[uuid.UUID] = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name: M[str] = db.Column(db.String(255), nullable=False, unique=True, index=True)
    description: M[Optional[str]] = db.Column(db.Text)
    
    # Timestamps
    created_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, index=True)
    updated_at: M[datetime] = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, onupdate=QuasDateTime.aware_utcnow)
    
    # Relationship to products (backref)
    products = relationship("Product", back_populates="product_material")
    
    def __repr__(self) -> str:
        return f"<ProductMaterial {self.id}, {self.name}>"
    
    @property
    def usage_count(self) -> int:
        """Get the count of products using this material."""
        return len(self.products) if self.products else 0
    
    def to_dict(self, include_products: bool = False) -> Dict[str, Any]:
        """Convert material to dictionary."""
        data = {
            "id": str(self.id),
            "name": self.name,
            "description": self.description or "",
            "usage_count": self.usage_count,
            "created_at": to_gmt1_or_none(self.created_at),
            "updated_at": to_gmt1_or_none(self.updated_at),
        }
        
        if include_products:
            data["products"] = [{"id": str(p.id), "name": p.name, "sku": p.sku} for p in self.products]
        
        return data

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
    
    # Material reference (nullable FK to ProductMaterial)
    material_id: M[Optional[uuid.UUID]] = db.Column(UUID(as_uuid=True), db.ForeignKey("product_material.id", ondelete="SET NULL"), nullable=True, index=True)
    
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
    images = relationship("Media", secondary="product_media", lazy="dynamic", backref="products")
    categories = db.relationship("ProductCategory", secondary=product_categories, backref=db.backref("products", lazy="dynamic"))
    product_material = relationship("ProductMaterial", back_populates="products")
    
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
            "material_id": str(self.material_id) if self.material_id else None,
            "material": self.product_material.to_dict() if self.product_material else None,
            "metadata": self.product_metadata or {},
            "meta_title": self.meta_title,
            "meta_description": self.meta_description,
            "meta_keywords": self.meta_keywords,
            "status": self.launch_status,  # Alias for launch_status
            "launch_status": self.launch_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        
        # Calculate price, color, and stock from variants (always, even if not including full variant objects)
        if self.variants:
            prices_ngn = [float(v.price_ngn) for v in self.variants if v.price_ngn]
            prices_usd = [float(v.price_usd) for v in self.variants if v.price_usd and v.price_usd]
            data["price_ngn"] = min(prices_ngn) if prices_ngn else None
            data["price_usd"] = min(prices_usd) if prices_usd else None
            data["price"] = data["price_ngn"]  # Alias for price_ngn
            
            # Extract available colors from variants
            colors = []
            for variant in self.variants:
                if variant.attributes and variant.attributes.get("color"):
                    color = variant.attributes.get("color")
                    if color and color not in colors:
                        colors.append(color)
            data["color"] = ", ".join(colors) if colors else ""
            
            # Calculate total stock (sum of all variant stocks)
            total_stock = sum(v.stock_quantity for v in self.variants)
            data["stock"] = total_stock
        else:
            data["price_ngn"] = None
            data["price_usd"] = None
            data["price"] = None
            data["color"] = ""
            data["stock"] = 0
        
        # Include product images
        images = [img.to_dict() for img in self.images.all()]
        data["images"] = images
        # Also include image URLs as a simple array for convenience
        data["image_urls"] = [img.file_url for img in self.images.all()]
        
        if include_variants:
            # Include variants with all details including prices
            data["variants"] = [v.to_dict(include_inventory=True) for v in self.variants]
        
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
    
    # Material reference (nullable FK to ProductMaterial - variant can have its own material)
    material_id: M[Optional[uuid.UUID]] = db.Column(UUID(as_uuid=True), db.ForeignKey("product_material.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Relationships
    product = relationship("Product", back_populates="variants")
    inventory = relationship("Inventory", back_populates="variant", uselist=False, cascade="all, delete-orphan")
    images = relationship("Media", secondary="variant_media", lazy="dynamic", backref="variants")
    variant_material = relationship("ProductMaterial", foreign_keys=[material_id])
    
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
    
    def to_dict(self, include_inventory: bool = False, include_product_info: bool = False) -> Dict[str, Any]:
        """Convert variant to dictionary."""
        # Extract color from attributes
        color = ""
        if self.attributes and isinstance(self.attributes, dict):
            color = self.attributes.get("color", "") or ""
        
        data = {
            "id": str(self.id),
            "product_id": str(self.product_id),
            "sku": self.sku,
            "price_ngn": float(self.price_ngn),
            "price_usd": float(self.price_usd) if self.price_usd else None,
            "price": float(self.price_ngn),  # Alias for price_ngn
            "weight_g": self.weight_g,
            "attributes": self.attributes or {},
            "color": color,
            "is_in_stock": self.is_in_stock,
            "stock_quantity": self.stock_quantity,
            "stock": self.stock_quantity,  # Alias for stock_quantity
            "material_id": str(self.material_id) if self.material_id else None,
            "material": self.variant_material.to_dict() if self.variant_material else None,
            "created_at": to_gmt1_or_none(self.created_at),
            "updated_at": to_gmt1_or_none(self.updated_at),
        }
        
        # Include variant images
        images = [img.to_dict() for img in self.images.all()]
        data["images"] = images
        data["image_urls"] = [img.file_url for img in self.images.all()]
        
        # Inherit fields from parent product
        if include_product_info and self.product:
            data["product_name"] = self.product.name
            data["product_slug"] = self.product.slug
            data["product_category"] = self.product.category
            data["description"] = self.product.description or ""
            data["care"] = self.product.care or ""
            data["details"] = self.product.details or ""
            data["material"] = self.product.material or ""
            # Include product images as well
            product_images = [img.to_dict() for img in self.product.images.all()]
            data["product_images"] = product_images
            data["product_image_urls"] = [img.file_url for img in self.product.images.all()]
        
        if include_inventory and self.inventory:
            data["inventory"] = self.inventory.to_dict()
        
        return data


# Association table for product-media many-to-many relationship
product_media = db.Table(
    "product_media",
    db.Column("product_id", UUID(as_uuid=True), db.ForeignKey("product.id", ondelete="CASCADE"), primary_key=True),
    db.Column("media_id", UUID(as_uuid=True), db.ForeignKey("media.id", ondelete="CASCADE"), primary_key=True),
)

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

