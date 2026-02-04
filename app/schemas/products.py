"""
Pydantic schemas for product-related endpoints.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from decimal import Decimal


class ProductVariantAttributes(BaseModel):
    """Product variant attributes schema."""
    length: Optional[str] = Field(None, description="Hair length in inches")
    texture: Optional[str] = Field(None, description="Hair texture")
    color: Optional[str] = Field(None, description="Hair color")
    lace_type: Optional[str] = Field(None, description="Lace type")
    density: Optional[str] = Field(None, description="Hair density")
    cap_size: Optional[str] = Field(None, description="Cap size")
    hair_type: Optional[str] = Field(None, description="Hair type")


class CreateProductVariantRequest(BaseModel):
    """Schema for creating a product variant."""
    sku: str = Field(..., min_length=1, max_length=100, description="Unique SKU")
    price_ngn: Decimal = Field(..., gt=0, description="Price in NGN")
    price_usd: Optional[Decimal] = Field(None, gt=0, description="Price in USD")
    weight_g: Optional[int] = Field(None, gt=0, description="Weight in grams")
    attributes: Optional[ProductVariantAttributes] = Field(None, description="Variant attributes (color, length, texture, etc.)")
    media_ids: Optional[List[str]] = Field(None, description="List of media IDs")


class CreateProductRequest(BaseModel):
    """Schema for creating a product."""
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    sku: Optional[str] = Field(None, min_length=1, max_length=100, description="Product SKU (auto-generated from name if not provided)")
    slug: Optional[str] = Field(None, max_length=255, description="URL-friendly slug (auto-generated if not provided)")
    description: Optional[str] = Field("", description="Product description")
    category: str = Field(..., description="Product category (string)")
    category_id: Optional[int] = Field(None, description="Optional category ID to link")
    care: Optional[str] = Field("", description="Product care instructions")
    details: Optional[str] = Field("", description="Product details")
    material_id: Optional[str] = Field(None, description="Optional material ID to link")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    meta_title: Optional[str] = Field(None, max_length=255, description="SEO meta title")
    meta_description: Optional[str] = Field(None, description="SEO meta description")
    meta_keywords: Optional[str] = Field(None, max_length=500, description="SEO meta keywords")
    status: Optional[str] = Field("In-Stock", description="Product status (default: In-Stock)")
    launch_status: Optional[str] = Field(None, description="Launch status (legacy field, use status instead)")
    variants: Optional[List[CreateProductVariantRequest]] = Field(None, description="Initial variants")


class UpdateProductRequest(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    sku: Optional[str] = Field(None, min_length=1, max_length=100, description="Product SKU (unique identifier)")
    slug: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    category_id: Optional[int] = None
    care: Optional[str] = None
    details: Optional[str] = None
    material_id: Optional[str] = Field(None, description="Material ID to link (set to empty string to unlink)")
    metadata: Optional[Dict[str, Any]] = None
    meta_title: Optional[str] = Field(None, max_length=255)
    meta_description: Optional[str] = None
    meta_keywords: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, description="Product status")
    launch_status: Optional[str] = None


class UpdateProductVariantRequest(BaseModel):
    """Schema for updating a product variant."""
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    price_ngn: Optional[Decimal] = Field(None, gt=0)
    price_usd: Optional[Decimal] = Field(None, gt=0)
    weight_g: Optional[int] = Field(None, gt=0)
    attributes: Optional[ProductVariantAttributes] = None
    media_ids: Optional[List[str]] = None


class ProductFilterRequest(BaseModel):
    """Schema for filtering products."""
    category: Optional[str] = None
    texture: Optional[str] = None
    length: Optional[str] = None
    color: Optional[str] = None
    lace_type: Optional[str] = None
    density: Optional[str] = None
    price_min: Optional[Decimal] = Field(None, ge=0)
    price_max: Optional[Decimal] = Field(None, ge=0)
    in_stock_only: Optional[bool] = Field(False, description="Filter to only in-stock items")
    search: Optional[str] = Field(None, description="Search term")
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order (asc/desc)")
    page: Optional[int] = Field(1, ge=1, description="Page number")
    per_page: Optional[int] = Field(20, ge=1, le=100, description="Items per page")


class InventoryAdjustRequest(BaseModel):
    """Schema for adjusting inventory."""
    variant_id: str = Field(..., description="Variant ID")
    quantity: int = Field(..., description="New quantity (or delta if using adjust_delta)")
    adjust_delta: Optional[bool] = Field(False, description="If True, quantity is added/subtracted from current")
    low_stock_threshold: Optional[int] = Field(None, ge=0, description="Update low stock threshold")







