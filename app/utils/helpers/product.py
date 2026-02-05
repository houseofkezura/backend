"""
Product helper functions for admin web interface.
"""

from __future__ import annotations

from typing import Optional
from flask import request
from slugify import slugify
import uuid
import random
import string

from app.extensions import db
from app.models.product import Product, ProductVariant, Inventory
from app.models.category import ProductCategory
from app.models.media import Media
from app.logging import log_error, log_event


def _get_category_code(category_name: str) -> str:
    """Map product category to 2-letter code for SKU generation."""
    category_map = {
        "Wigs": "HW",
        "Jewelry": "JW",
        "Perfume": "PF",
        "Skincare": "SC",
        "Supplements": "SP",
        "Misc": "MC",
    }
    return category_map.get(category_name, category_name[:2].upper() if category_name else "PR")


def _generate_random_alphanumeric(length: int = 4) -> str:
    """Generate random alphanumeric string."""
    chars = string.ascii_uppercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def _generate_sku(category_name: str) -> str:
    """Generate SKU in format: KZ-[CATEGORY]-[4 random alphanumeric]."""
    category_code = _get_category_code(category_name)
    random_code = _generate_random_alphanumeric(4)
    return f"KZ-{category_code}-{random_code}"


def fetch_product(identifier: str) -> Optional[Product]:
    """
    Fetch a product by ID (UUID) or slug.
    
    Args:
        identifier: Product ID (UUID string) or slug
        
    Returns:
        Product instance or None if not found
    """
    try:
        # Try as UUID first
        try:
            product_uuid = uuid.UUID(identifier)
            product = Product.query.get(product_uuid)
            if product:
                return product
        except ValueError:
            pass
        
        # Try as slug
        product = Product.query.filter_by(slug=identifier).first()
        return product
    except Exception as e:
        log_error(f"Failed to fetch product {identifier}", error=e)
        return None


from app.utils.helpers.media import save_media

def save_product(form_data: dict, product: Optional[Product] = None, files: dict = None) -> Product:
    """
    Create or update a product from form data.
    
    Handles:
    - SKU and slug generation
    - Category linking
    - Multiple category relationships
    - Product images
    - Variants with pricing and inventory
    - Material linking
    
    Args:
        form_data: Form data dictionary (from request.form)
        product: Existing product instance (for updates) or None (for creates)
        files: Files uploaded (from request.files)
        
    Returns:
        Created or updated Product instance
        
    Raises:
        ValueError: For validation errors (duplicate SKU/slug, invalid category, etc.)
    """
    try:
        # Extract form data
        name = form_data.get('name', '').strip()
        if not name:
            raise ValueError('Product name is required')
        
        description = form_data.get('description', '').strip()
        care = form_data.get('care', '').strip()
        details = form_data.get('details', '').strip()
        material_id_str = form_data.get('material', '').strip()
        colors = form_data.get('colors', '').strip()
        
        # Get primary category
        product_category_id = form_data.get('product_category', '').strip()
        if not product_category_id:
            raise ValueError('Product category is required')
        
        try:
            category_uuid = uuid.UUID(product_category_id)
            category_model = ProductCategory.query.get(category_uuid)
            if not category_model:
                raise ValueError('Invalid category selected')
            category_name = category_model.name
        except (ValueError, TypeError) as e:
            if isinstance(e, ValueError) and 'Invalid category' in str(e):
                raise
            raise ValueError('Invalid category ID format')
        
        # Get additional categories (from checkboxes)
        # Handle both list and single value
        selected_category_ids = form_data.get('categories', [])
        if isinstance(selected_category_ids, str):
            selected_category_ids = [selected_category_ids] if selected_category_ids else []
        elif not isinstance(selected_category_ids, list):
            selected_category_ids = []
        
        # Generate slug if not provided or if creating new product
        product_slug = form_data.get('slug', '').strip()
        if not product_slug:
            product_slug = slugify(name)
            # Ensure uniqueness
            base_slug = product_slug
            counter = 1
            while Product.query.filter_by(slug=product_slug).filter(
                Product.id != product.id if product else None
            ).first():
                product_slug = f"{base_slug}-{counter}"
                counter += 1
        else:
            # Check slug uniqueness if provided
            existing = Product.query.filter_by(slug=product_slug).filter(
                Product.id != product.id if product else None
            ).first()
            if existing:
                raise ValueError('Product with this slug already exists')
        
        # Generate SKU if creating new product
        if product:
            # Update existing product
            product.name = name
            product.description = description or ""
            product.care = care or ""
            product.details = details or ""
            # product.material = material or "" # REMOVED: potentially incorrect field
            product.category = category_name
            product.slug = product_slug
            
            # Update Material ID
            if material_id_str:
                try:
                    product.material_id = uuid.UUID(material_id_str)
                except ValueError:
                    product.material_id = None
            else:
                product.material_id = None
            
            # Update metadata (preserve existing, update colors)
            if not product.product_metadata:
                product.product_metadata = {}
            if colors:
                product.product_metadata["colors"] = colors
            elif "colors" in product.product_metadata:
                # Remove colors if empty
                del product.product_metadata["colors"]
            
            # Update category relationships
            product.categories = []
            if category_model:
                product.categories.append(category_model)
            
            # Add additional categories
            for cat_id in selected_category_ids:
                try:
                    cat_uuid = uuid.UUID(cat_id)
                    additional_cat = ProductCategory.query.get(cat_uuid)
                    if additional_cat and additional_cat not in product.categories:
                        product.categories.append(additional_cat)
                except (ValueError, TypeError):
                    continue
            
            # Handle Image Uploads
            if files and 'images' in files:
                uploaded_files = files.getlist('images')
                for file in uploaded_files:
                    if file and file.filename:
                        media = save_media(file)
                        product.images.append(media)

            db.session.flush()
            db.session.commit()
            
            # Refresh product
            product = Product.query.get(product.id)
            return product
        else:
            # Create new product
            # Generate SKU
            max_attempts = 100
            product_sku = None
            for _ in range(max_attempts):
                product_sku = _generate_sku(category_name)
                if not Product.query.filter_by(sku=product_sku).first():
                    break
            else:
                # Fallback
                category_code = _get_category_code(category_name)
                product_sku = f"KZ-{category_code}-{str(uuid.uuid4())[:4].upper()}"
            
            # Create product
            new_product = Product()
            new_product.name = name
            new_product.sku = product_sku
            new_product.slug = product_slug
            new_product.description = description or ""
            new_product.category = category_name
            new_product.care = care or ""
            new_product.details = details or ""
            # new_product.material = material or "" # REMOVED
            new_product.launch_status = "In-Stock"  # Default status

            # Set Material ID
            if material_id_str:
                try:
                    new_product.material_id = uuid.UUID(material_id_str)
                except ValueError:
                    new_product.material_id = None
            
            # Store colors in metadata if provided
            if colors:
                new_product.product_metadata = {"colors": colors}
            
            db.session.add(new_product)
            db.session.flush()
            
            # Link primary category
            if category_model:
                new_product.categories.append(category_model)
            
            # Link additional categories
            for cat_id in selected_category_ids:
                try:
                    cat_uuid = uuid.UUID(cat_id)
                    additional_cat = ProductCategory.query.get(cat_uuid)
                    if additional_cat and additional_cat not in new_product.categories:
                        new_product.categories.append(additional_cat)
                except (ValueError, TypeError):
                    continue
            
            db.session.commit()
            
            # Handle variants if provided
            if 'variants_data' in form_data and form_data['variants_data']:
                _handle_variants(new_product if not product else product, form_data['variants_data'])
            
            # Handle Image Uploads (for new product)
            if files and 'images' in files:
                uploaded_files = files.getlist('images')
                for file in uploaded_files:
                    if file and file.filename:
                        media = save_media(file)
                        new_product.images.append(media)
            
            db.session.commit()

            # Refresh product
            new_product = Product.query.get(new_product.id)
            return new_product
            
    except ValueError as e:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        log_error('An error occurred while saving product', e)
        raise ValueError(f'Failed to save product: {str(e)}')


def _handle_variants(product: Product, variants_data: str):
    """
    Create or update product variants from JSON data.
    
    Args:
        product: Product instance
        variants_data: JSON string containing variants array
    """
    import json
    
    try:
        variants = json.loads(variants_data) if isinstance(variants_data, str) else variants_data
        
        for variant_data in variants:
            # Generate variant SKU
            variant_sku = variant_data.get('sku', '')
            if not variant_sku:
                # Auto-generate: PRODUCT_SKU-VARIANT_SUFFIX
                variant_name = variant_data.get('name', '')
                suffix = variant_name.replace(' ', '-').replace('/', '-')[:10].upper()
                variant_sku = f"{product.sku}-{suffix}"
            
            # Check if variant already exists
            existing_variant = ProductVariant.query.filter_by(sku=variant_sku).first()
            if existing_variant and existing_variant.product_id != product.id:
                raise ValueError(f"Variant SKU '{variant_sku}' already exists")
            
            if existing_variant:
                # Update existing variant
                variant = existing_variant
            else:
                # Create new variant
                variant = ProductVariant()
                variant.product_id = product.id
                variant.sku = variant_sku
                db.session.add(variant)
            
            # Set variant fields
            variant.price_ngn = float(variant_data.get('price_ngn', 0))
            variant.price_usd = float(variant_data.get('price_usd', 0)) if variant_data.get('price_usd') else None
            variant.weight_g = int(variant_data.get('weight_g', 0)) if variant_data.get('weight_g') else None
            
            # Set attributes from variation types/values
            attributes = variant_data.get('attributes', {})
            if isinstance(attributes, str):
                attributes = json.loads(attributes)
            variant.attributes = attributes
            
            db.session.flush()
            
            # Create or update inventory
            inventory = Inventory.query.filter_by(variant_id=variant.id).first()
            if not inventory:
                inventory = Inventory()
                inventory.variant_id = variant.id
                db.session.add(inventory)
            
            inventory.quantity = int(variant_data.get('quantity', 0))
            inventory.low_stock_threshold = int(variant_data.get('low_stock_threshold', 5))
        
        db.session.commit()
        
    except json.JSONDecodeError as e:
        log_error('Failed to parse variants JSON', e)
        raise ValueError('Invalid variants data format')
    except Exception as e:
        db.session.rollback()
        log_error('Failed to handle variants', e)
        raise ValueError(f'Failed to save variants: {str(e)}')

