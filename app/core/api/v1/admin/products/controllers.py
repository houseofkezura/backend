"""
Admin product controller.
"""

from __future__ import annotations

from flask import Response, request
from slugify import slugify
import uuid

from app.extensions import db
from app.models.product import Product, ProductVariant, Inventory
from app.schemas.products import CreateProductRequest, UpdateProductRequest, CreateProductVariantRequest, UpdateProductVariantRequest
from app.utils.helpers.api_response import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class AdminProductController:
    """Controller for admin product endpoints."""

    @staticmethod
    def create_product() -> Response:
        """
        Create a new product with optional variants.
        
        Requires admin authentication.
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            payload = CreateProductRequest.model_validate(request.get_json())
            
            # Generate slug if not provided
            product_slug = payload.slug or slugify(payload.name)
            
            # Check if slug exists
            existing = Product.query.filter_by(slug=product_slug).first()
            if existing:
                return error_response("Product with this slug already exists", 409)
            
            # Create product
            product = Product()
            product.name = payload.name
            product.slug = product_slug
            product.description = payload.description
            product.category = payload.category
            product.product_metadata = payload.metadata or {}
            product.meta_title = payload.meta_title
            product.meta_description = payload.meta_description
            product.meta_keywords = payload.meta_keywords
            product.launch_status = payload.launch_status or "In Stock"
            
            db.session.add(product)
            db.session.flush()
            
            # Create variants if provided
            if payload.variants:
                for variant_data in payload.variants:
                    variant = ProductVariant()
                    variant.product_id = product.id
                    variant.sku = variant_data.sku
                    variant.price_ngn = variant_data.price_ngn
                    variant.price_usd = variant_data.price_usd
                    variant.weight_g = variant_data.weight_g
                    variant.attributes = variant_data.attributes.dict() if variant_data.attributes else {}
                    
                    db.session.add(variant)
                    db.session.flush()
                    
                    # Create inventory
                    inventory = Inventory()
                    inventory.variant_id = variant.id
                    inventory.quantity = 0
                    inventory.low_stock_threshold = 5
                    db.session.add(inventory)
                    
                    # Store media IDs in variant attributes
                    if variant_data.media_ids:
                        if not variant.attributes:
                            variant.attributes = {}
                        variant.attributes["media_ids"] = variant_data.media_ids
            
            db.session.commit()
            
            log_event(f"Product created: {product.id} by admin {current_user.id}")
            
            return success_response(
                "Product created successfully",
                201,
                {"product": product.to_dict(include_variants=True)}
            )
        except Exception as e:
            log_error("Failed to create product", error=e)
            db.session.rollback()
            return error_response("Failed to create product", 500)

    @staticmethod
    def update_product(product_id: str) -> Response:
        """
        Update a product.
        
        Args:
            product_id: Product ID
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                product_uuid = uuid.UUID(product_id)
            except ValueError:
                return error_response("Invalid product ID format", 400)
            
            product = Product.query.get(product_uuid)
            if not product:
                return error_response("Product not found", 404)
            
            payload = UpdateProductRequest.model_validate(request.get_json())
            
            # Update fields
            if payload.name is not None:
                product.name = payload.name
            if payload.slug is not None:
                # Check slug uniqueness
                existing = Product.query.filter_by(slug=payload.slug).filter(Product.id != product_uuid).first()
                if existing:
                    return error_response("Slug already in use", 409)
                product.slug = payload.slug
            if payload.description is not None:
                product.description = payload.description
            if payload.category is not None:
                product.category = payload.category
            if payload.metadata is not None:
                product.product_metadata = payload.metadata
            if payload.meta_title is not None:
                product.meta_title = payload.meta_title
            if payload.meta_description is not None:
                product.meta_description = payload.meta_description
            if payload.meta_keywords is not None:
                product.meta_keywords = payload.meta_keywords
            if payload.launch_status is not None:
                product.launch_status = payload.launch_status
            
            db.session.commit()
            
            log_event(f"Product updated: {product_id} by admin {current_user.id}")
            
            return success_response(
                "Product updated successfully",
                200,
                {"product": product.to_dict(include_variants=True)}
            )
        except Exception as e:
            log_error(f"Failed to update product {product_id}", error=e)
            db.session.rollback()
            return error_response("Failed to update product", 500)

