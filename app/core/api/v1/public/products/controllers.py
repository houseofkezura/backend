"""
Product controller for public product endpoints.
"""

from __future__ import annotations

from flask import Response, request
from sqlalchemy import or_, and_, desc, asc
from sqlalchemy.orm import Query
from typing import Optional

from app.extensions import db
from app.models.product import Product, ProductVariant, Inventory
from app.schemas.products import ProductFilterRequest
from quas_utils.api import success_response, error_response
from app.logging import log_error, log_event


class ProductController:
    """Controller for public product endpoints."""

    @staticmethod
    def list_products() -> Response:
        """
        List products with filtering, sorting, and pagination.
        
        Public endpoint - no authentication required.
        """
        try:
            # Parse query parameters
            filters = ProductFilterRequest.model_validate(request.args.to_dict())
            
            # Build base query
            query: Query = Product.query
            
            # Apply search filter
            if filters.search:
                query = Product.add_search_filters(query, filters.search)
            
            # Apply category filter
            if filters.category:
                query = query.filter(Product.category == filters.category)
            
            # Apply launch status filter (default to in stock)
            if filters.in_stock_only:
                query = query.filter(Product.launch_status.in_([
                    "In Stock", "New Drop", "Limited Edition"
                ]))
            
            # Apply sorting
            sort_field = getattr(Product, filters.sort_by, Product.created_at)
            if filters.sort_order == "asc":
                query = query.order_by(asc(sort_field))
            else:
                query = query.order_by(desc(sort_field))
            
            # Get total count before pagination
            total = query.count()
            
            # Apply pagination
            per_page = filters.per_page
            page = filters.page
            offset = (page - 1) * per_page
            products = query.offset(offset).limit(per_page).all()
            
            # Filter variants by attributes if provided
            # This is a simplified approach - in production, you'd want more sophisticated filtering
            product_data = []
            for product in products:
                variants = product.variants
                
                # Apply variant-level filters
                if filters.texture or filters.length or filters.color or filters.lace_type or filters.density:
                    filtered_variants = []
                    for variant in variants:
                        attrs = variant.attributes or {}
                        match = True
                        
                        if filters.texture and attrs.get("texture") != filters.texture:
                            match = False
                        if filters.length and attrs.get("length") != filters.length:
                            match = False
                        if filters.color and attrs.get("color") != filters.color:
                            match = False
                        if filters.lace_type and attrs.get("lace_type") != filters.lace_type:
                            match = False
                        if filters.density and attrs.get("density") != filters.density:
                            match = False
                        
                        if match:
                            filtered_variants.append(variant)
                    
                    # Only include product if it has matching variants
                    if not filtered_variants:
                        continue
                    variants = filtered_variants
                
                # Apply price filters
                if filters.price_min or filters.price_max:
                    price_filtered_variants = []
                    for variant in variants:
                        price = float(variant.price_ngn)
                        if filters.price_min and price < float(filters.price_min):
                            continue
                        if filters.price_max and price > float(filters.price_max):
                            continue
                        price_filtered_variants.append(variant)
                    
                    if not price_filtered_variants:
                        continue
                    variants = price_filtered_variants
                
                # Apply stock filter
                if filters.in_stock_only:
                    variants = [v for v in variants if v.is_in_stock]
                    if not variants:
                        continue
                
                product_dict = product.to_dict(include_variants=False)
                product_dict["variants"] = [v.to_dict(include_inventory=True) for v in variants]
                product_data.append(product_dict)
            
            return success_response(
                "Products retrieved successfully",
                200,
                {
                    "products": product_data,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": total,
                        "pages": (total + per_page - 1) // per_page,
                    }
                }
            )
        except Exception as e:
            log_error("Failed to list products", error=e)
            return error_response("Failed to retrieve products", 500)

    @staticmethod
    def get_product(slug: str) -> Response:
        """
        Get a single product by slug with all variants.
        
        Public endpoint - no authentication required.
        """
        try:
            product = Product.query.filter_by(slug=slug).first()
            
            if not product:
                return error_response("Product not found", 404)
            
            product_data = product.to_dict(include_variants=True)
            
            # Include inventory info for each variant
            for variant_data in product_data.get("variants", []):
                variant_id = variant_data["id"]
                variant = ProductVariant.query.get(variant_id)
                if variant:
                    variant_data["inventory"] = variant.inventory.to_dict() if variant.inventory else None
            
            return success_response(
                "Product retrieved successfully",
                200,
                {"product": product_data}
            )
        except Exception as e:
            log_error("Failed to get product", error=e)
            return error_response("Failed to retrieve product", 500)

    @staticmethod
    def search_products() -> Response:
        """
        Lightweight search endpoint for autocomplete.
        
        Public endpoint - no authentication required.
        """
        try:
            q = request.args.get("q", "").strip()
            
            if not q or len(q) < 2:
                return success_response(
                    "Search results",
                    200,
                    {"results": []}
                )
            
            # Simple search on product name and description
            query = Product.query.filter(
                or_(
                    Product.name.ilike(f"%{q}%"),
                    Product.description.ilike(f"%{q}%"),
                )
            ).limit(10)
            
            products = query.all()
            
            results = [
                {
                    "id": str(p.id),
                    "name": p.name,
                    "slug": p.slug,
                    "category": p.category,
                }
                for p in products
            ]
            
            return success_response(
                "Search results",
                200,
                {"results": results}
            )
        except Exception as e:
            log_error("Failed to search products", error=e)
            return error_response("Failed to search products", 500)

    @staticmethod
    def get_product_variants(product_id: str) -> Response:
        """
        Get all variants for a product.
        
        Public endpoint - no authentication required.
        """
        try:
            product = Product.query.get(product_id)
            
            if not product:
                return error_response("Product not found", 404)
            
            variants = [v.to_dict(include_inventory=True) for v in product.variants]
            
            return success_response(
                "Variants retrieved successfully",
                200,
                {"variants": variants}
            )
        except Exception as e:
            log_error("Failed to get variants", error=e)
            return error_response("Failed to retrieve variants", 500)





