"""
Admin product controller.
"""

from __future__ import annotations

from flask import Response, request
from slugify import slugify
import uuid
import re
import random
import string

from app.extensions import db
from app.models.product import Product, ProductVariant, Inventory, ProductMaterial
from app.models.category import ProductCategory
from app.models.media import Media
from app.schemas.products import CreateProductRequest, UpdateProductRequest, CreateProductVariantRequest, UpdateProductVariantRequest
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.utils.helpers.media import save_media
from app.logging import log_error, log_event


class AdminProductController:
    """Controller for admin product endpoints."""

    @staticmethod
    def _get_category_code(category: str) -> str:
        """Map product category to 2-letter code for SKU generation."""
        category_map = {
            "Wigs": "WG",
            "Bundles": "BD",
            "Hair Care": "HC",
        }
        # Default to first 2 uppercase letters if not in map
        return category_map.get(category, category[:2].upper() if category else "PR")

    @staticmethod
    def _generate_random_alphanumeric(length: int = 4) -> str:
        """Generate random alphanumeric string (uppercase letters and digits)."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(length))

    @staticmethod
    def _generate_sku(category: str) -> str:
        """Generate SKU in format: KZ-[CATEGORY]-[4 random alphanumeric]."""
        category_code = AdminProductController._get_category_code(category)
        random_code = AdminProductController._generate_random_alphanumeric(4)
        return f"KZ-{category_code}-{random_code}"

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
            
            # Generate SKU if not provided
            product_sku = payload.sku
            if not product_sku:
                # Generate SKU in format: KZ-[CATEGORY]-[4 random alphanumeric]
                max_attempts = 100
                for _ in range(max_attempts):
                    product_sku = AdminProductController._generate_sku(payload.category)
                    # Check if SKU already exists
                    if not Product.query.filter_by(sku=product_sku).first():
                        break
                else:
                    # If all attempts failed, use UUID fallback
                    category_code = AdminProductController._get_category_code(payload.category)
                    product_sku = f"KZ-{category_code}-{str(uuid.uuid4())[:4].upper()}"
            else:
                # Check if provided SKU exists
                existing_sku = Product.query.filter_by(sku=product_sku).first()
                if existing_sku:
                    return error_response("Product with this SKU already exists", 409)
            
            # Create product
            product = Product()
            product.name = payload.name
            product.sku = product_sku
            product.slug = product_slug
            product.description = payload.description or ""
            # Resolve category: prefer category_id if provided; keep string field unchanged if not found
            category_name = payload.category
            category_model = None
            if payload.category_id:
                category_model = ProductCategory.query.get(payload.category_id)
                if category_model:
                    category_name = category_model.name
            product.category = category_name
            product.care = payload.care or ""
            product.details = payload.details or ""
            
            # Link material if provided
            if payload.material_id:
                try:
                    material_uuid = uuid.UUID(payload.material_id)
                    material = ProductMaterial.query.get(material_uuid)
                    if material:
                        product.material_id = material_uuid
                    else:
                        return error_response("Material not found", 404)
                except ValueError:
                    return error_response("Invalid material ID format", 400)
            
            product.product_metadata = payload.metadata or {}
            product.meta_title = payload.meta_title
            product.meta_description = payload.meta_description
            product.meta_keywords = payload.meta_keywords
            # Use status if provided, otherwise launch_status, otherwise default to "In-Stock"
            product.launch_status = payload.status or payload.launch_status or "In-Stock"
            
            db.session.add(product)
            db.session.flush()

            # Link categories relationship if category_id provided
            if category_model:
                product.categories.append(category_model)
            
            # Create variants if provided
            if payload.variants:
                for variant_data in payload.variants:
                    variant = ProductVariant()
                    variant.product_id = product.id
                    variant.sku = variant_data.sku
                    variant.price_ngn = variant_data.price_ngn
                    variant.price_usd = variant_data.price_usd
                    variant.weight_g = variant_data.weight_g
                    # Convert attributes to dict, handling both Pydantic model and dict
                    if variant_data.attributes:
                        if isinstance(variant_data.attributes, dict):
                            variant.attributes = variant_data.attributes
                        else:
                            variant.attributes = variant_data.attributes.dict(exclude_none=True)
                    else:
                        variant.attributes = {}
                    
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
            if payload.sku is not None:
                # Check SKU uniqueness
                existing_sku = Product.query.filter_by(sku=payload.sku).filter(Product.id != product_uuid).first()
                if existing_sku:
                    return error_response("SKU already in use", 409)
                product.sku = payload.sku
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
            if payload.category_id is not None:
                cat_model = ProductCategory.query.get(payload.category_id)
                if cat_model:
                    product.category = cat_model.name
                    product.categories = [cat_model]
            if payload.care is not None:
                product.care = payload.care
            if payload.details is not None:
                product.details = payload.details
            if payload.material_id is not None:
                if payload.material_id == "":
                    # Unlink material
                    product.material_id = None
                else:
                    try:
                        material_uuid = uuid.UUID(payload.material_id)
                        material = ProductMaterial.query.get(material_uuid)
                        if material:
                            product.material_id = material_uuid
                        else:
                            return error_response("Material not found", 404)
                    except ValueError:
                        return error_response("Invalid material ID format", 400)
            if payload.metadata is not None:
                product.product_metadata = payload.metadata
            if payload.meta_title is not None:
                product.meta_title = payload.meta_title
            if payload.meta_description is not None:
                product.meta_description = payload.meta_description
            if payload.meta_keywords is not None:
                product.meta_keywords = payload.meta_keywords
            # Update status (prefer status over launch_status for consistency)
            if payload.status is not None:
                product.launch_status = payload.status
            elif payload.launch_status is not None:
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

    @staticmethod
    def list_products() -> Response:
        """
        List all products with optional filtering and pagination.
        
        Requires admin authentication.
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            # Get query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            search = request.args.get('search', type=str)
            category = request.args.get('category', type=str)
            launch_status = request.args.get('launch_status', type=str)
            
            # Build query
            query = Product.query
            
            if search:
                query = query.filter(
                    db.or_(
                        Product.name.ilike(f'%{search}%'),
                        Product.description.ilike(f'%{search}%')
                    )
                )
            
            if category:
                query = query.filter_by(category=category)
            
            if launch_status:
                query = query.filter_by(launch_status=launch_status)
            
            # Paginate
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            products = [p.to_dict(include_variants=True) for p in pagination.items]
            
            return success_response(
                "Products retrieved successfully",
                200,
                {
                    "products": products,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages
                    }
                }
            )
        except Exception as e:
            log_error("Failed to list products", error=e)
            return error_response("Failed to retrieve products", 500)

    @staticmethod
    def get_product(product_id: str) -> Response:
        """
        Get a single product by ID.
        
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
            
            return success_response(
                "Product retrieved successfully",
                200,
                {"product": product.to_dict(include_variants=True)}
            )
        except Exception as e:
            log_error(f"Failed to get product {product_id}", error=e)
            return error_response("Failed to retrieve product", 500)

    @staticmethod
    def delete_product(product_id: str) -> Response:
        """
        Delete a product.
        
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
            
            db.session.delete(product)
            db.session.commit()
            
            log_event(f"Product deleted: {product_id} by admin {current_user.id}")
            
            return success_response("Product deleted successfully", 200)
        except Exception as e:
            log_error(f"Failed to delete product {product_id}", error=e)
            db.session.rollback()
            return error_response("Failed to delete product", 500)

    @staticmethod
    def create_variant(product_id: str) -> Response:
        """
        Create a variant for a product.
        
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
            
            # Handle both single variant object and wrapped in 'variants' array
            request_data = request.get_json()
            if not request_data:
                return error_response("Request body is required", 400)
            
            # If payload is wrapped in 'variants' array, extract first variant
            if isinstance(request_data, dict) and 'variants' in request_data:
                if isinstance(request_data['variants'], list) and len(request_data['variants']) > 0:
                    request_data = request_data['variants'][0]
                else:
                    return error_response("Variants array is empty", 400)
            
            payload = CreateProductVariantRequest.model_validate(request_data)
            
            # Check SKU uniqueness
            existing = ProductVariant.query.filter_by(sku=payload.sku).first()
            if existing:
                return error_response("Variant with this SKU already exists", 409)
            
            variant = ProductVariant()
            variant.product_id = product.id
            variant.sku = payload.sku
            variant.price_ngn = payload.price_ngn
            variant.price_usd = payload.price_usd
            variant.weight_g = payload.weight_g
            # Convert attributes to dict, handling both Pydantic model and dict
            if payload.attributes:
                if isinstance(payload.attributes, dict):
                    variant.attributes = payload.attributes
                else:
                    variant.attributes = payload.attributes.dict(exclude_none=True)
            else:
                variant.attributes = {}
            
            if payload.media_ids:
                if not variant.attributes:
                    variant.attributes = {}
                variant.attributes["media_ids"] = payload.media_ids
            
            db.session.add(variant)
            db.session.flush()
            
            # Create inventory
            inventory = Inventory()
            inventory.variant_id = variant.id
            inventory.quantity = 0
            inventory.low_stock_threshold = 5
            db.session.add(inventory)
            
            db.session.commit()
            
            log_event(f"Variant created: {variant.id} for product {product_id} by admin {current_user.id}")
            
            return success_response(
                "Variant created successfully",
                201,
                {"variant": variant.to_dict()}
            )
        except Exception as e:
            log_error(f"Failed to create variant for product {product_id}", error=e)
            db.session.rollback()
            return error_response("Failed to create variant", 500)

    @staticmethod
    def update_variant(product_id: str, variant_id: str) -> Response:
        """
        Update a product variant.
        
        Args:
            product_id: Product ID
            variant_id: Variant ID
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                product_uuid = uuid.UUID(product_id)
                variant_uuid = uuid.UUID(variant_id)
            except ValueError:
                return error_response("Invalid ID format", 400)
            
            variant = ProductVariant.query.filter_by(id=variant_uuid, product_id=product_uuid).first()
            if not variant:
                return error_response("Variant not found", 404)
            
            payload = UpdateProductVariantRequest.model_validate(request.get_json())
            
            # Update fields
            if payload.sku is not None:
                # Check SKU uniqueness
                existing = ProductVariant.query.filter_by(sku=payload.sku).filter(ProductVariant.id != variant_uuid).first()
                if existing:
                    return error_response("SKU already in use", 409)
                variant.sku = payload.sku
            if payload.price_ngn is not None:
                variant.price_ngn = payload.price_ngn
            if payload.price_usd is not None:
                variant.price_usd = payload.price_usd
            if payload.weight_g is not None:
                variant.weight_g = payload.weight_g
            if payload.attributes is not None:
                # Convert attributes to dict, handling both Pydantic model and dict
                if isinstance(payload.attributes, dict):
                    variant.attributes = payload.attributes
                else:
                    variant.attributes = payload.attributes.dict(exclude_none=True)
            if payload.media_ids is not None:
                if not variant.attributes:
                    variant.attributes = {}
                variant.attributes["media_ids"] = payload.media_ids
            
            db.session.commit()
            
            log_event(f"Variant updated: {variant_id} by admin {current_user.id}")
            
            return success_response(
                "Variant updated successfully",
                200,
                {"variant": variant.to_dict()}
            )
        except Exception as e:
            log_error(f"Failed to update variant {variant_id}", error=e)
            db.session.rollback()
            return error_response("Failed to update variant", 500)

    @staticmethod
    def delete_variant(product_id: str, variant_id: str) -> Response:
        """
        Delete a product variant.
        
        Args:
            product_id: Product ID
            variant_id: Variant ID
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                product_uuid = uuid.UUID(product_id)
                variant_uuid = uuid.UUID(variant_id)
            except ValueError:
                return error_response("Invalid ID format", 400)
            
            variant = ProductVariant.query.filter_by(id=variant_uuid, product_id=product_uuid).first()
            if not variant:
                return error_response("Variant not found", 404)
            
            db.session.delete(variant)
            db.session.commit()
            
            log_event(f"Variant deleted: {variant_id} by admin {current_user.id}")
            
            return success_response("Variant deleted successfully", 200)
        except Exception as e:
            log_error(f"Failed to delete variant {variant_id}", error=e)
            db.session.rollback()
            return error_response("Failed to delete variant", 500)

    @staticmethod
    def add_product_images(product_id: str) -> Response:
        """
        Add images to a product.
        
        Accepts multiple image files and associates them with the product.
        
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
            
            # Get files from request (can be single file or multiple)
            files = request.files.getlist('images') or request.files.getlist('image')
            
            if not files or len(files) == 0:
                return error_response("No image files provided", 400)
            
            uploaded_images = []
            errors = []
            
            for file in files:
                if not file or file.filename == '':
                    continue
                
                try:
                    # Validate file type (only images)
                    filename = file.filename.lower()
                    if not any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                        errors.append(f"{file.filename}: Invalid file type. Only images are allowed.")
                        continue
                    
                    # Save media using helper
                    media = save_media(file)
                    
                    # Associate with product using relationship
                    product.images.append(media)
                    db.session.flush()  # Flush to get media ID
                    
                    uploaded_images.append(media.to_dict())
                    
                except Exception as e:
                    log_error(f"Failed to upload image {file.filename}", error=e)
                    errors.append(f"{file.filename}: {str(e)}")
                    # Don't rollback here - continue with other files
                    # Only rollback if commit fails at the end
                    continue
            
            if not uploaded_images:
                db.session.rollback()
                return error_response(
                    f"Failed to upload images. Errors: {'; '.join(errors)}" if errors else "No valid images provided",
                    400
                )
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                log_error("Failed to commit product images", error=e)
                return error_response("Failed to save images", 500)
            
            log_event(f"Added {len(uploaded_images)} images to product {product_id} by admin {current_user.id}")
            
            response_message = f"Successfully uploaded {len(uploaded_images)} image(s)"
            if errors:
                response_message += f". {len(errors)} file(s) failed: {'; '.join(errors)}"
            
            return success_response(
                response_message,
                201,
                {
                    "product_id": str(product.id),
                    "images": uploaded_images,
                    "total_images": len(uploaded_images),
                    "errors": errors if errors else None
                }
            )
        except Exception as e:
            log_error(f"Failed to add images to product {product_id}", error=e)
            db.session.rollback()
            return error_response("Failed to upload images", 500)

    @staticmethod
    def remove_product_image(product_id: str, image_id: str) -> Response:
        """
        Remove an image from a product.
        
        Args:
            product_id: Product ID
            image_id: Media ID to remove
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                product_uuid = uuid.UUID(product_id)
                image_uuid = uuid.UUID(image_id)
            except ValueError:
                return error_response("Invalid ID format", 400)
            
            product = Product.query.get(product_uuid)
            if not product:
                return error_response("Product not found", 404)
            
            # Check if image is associated with product
            media = Media.query.get(image_uuid)
            if not media:
                return error_response("Image not found", 404)
            
            if media not in product.images.all():
                return error_response("Image not associated with this product", 404)
            
            # Remove association using relationship
            product.images.remove(media)
            
            db.session.commit()
            
            log_event(f"Removed image {image_id} from product {product_id} by admin {current_user.id}")
            
            return success_response("Image removed successfully", 200)
        except Exception as e:
            log_error(f"Failed to remove image from product {product_id}", error=e)
            db.session.rollback()
            return error_response("Failed to remove image", 500)

    @staticmethod
    def add_variant_images(product_id: str, variant_id: str) -> Response:
        """
        Add images to a product variant.
        
        Accepts multiple image files and associates them with the variant.
        
        Args:
            product_id: Product ID
            variant_id: Variant ID
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                product_uuid = uuid.UUID(product_id)
                variant_uuid = uuid.UUID(variant_id)
            except ValueError:
                return error_response("Invalid ID format", 400)
            
            product = Product.query.get(product_uuid)
            if not product:
                return error_response("Product not found", 404)
            
            variant = ProductVariant.query.filter_by(id=variant_uuid, product_id=product_uuid).first()
            if not variant:
                return error_response("Variant not found", 404)
            
            # Get files from request (can be single file or multiple)
            files = request.files.getlist('images') or request.files.getlist('image')
            
            if not files or len(files) == 0:
                return error_response("No image files provided", 400)
            
            uploaded_images = []
            errors = []
            
            for file in files:
                if not file or file.filename == '':
                    continue
                
                try:
                    # Validate file type (only images)
                    filename = file.filename.lower()
                    if not any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']):
                        errors.append(f"{file.filename}: Invalid file type. Only images are allowed.")
                        continue
                    
                    # Save media using helper
                    media = save_media(file)
                    
                    # Associate with variant using relationship
                    variant.images.append(media)
                    db.session.flush()  # Flush to get media ID
                    
                    uploaded_images.append(media.to_dict())
                    
                except Exception as e:
                    log_error(f"Failed to upload image {file.filename}", error=e)
                    errors.append(f"{file.filename}: {str(e)}")
                    # Don't rollback here - continue with other files
                    continue
            
            if not uploaded_images:
                db.session.rollback()
                return error_response(
                    f"Failed to upload images. Errors: {'; '.join(errors)}" if errors else "No valid images provided",
                    400
                )
            
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                log_error("Failed to commit variant images", error=e)
                return error_response("Failed to save images", 500)
            
            log_event(f"Added {len(uploaded_images)} images to variant {variant_id} by admin {current_user.id}")
            
            response_message = f"Successfully uploaded {len(uploaded_images)} image(s)"
            if errors:
                response_message += f". {len(errors)} file(s) failed: {'; '.join(errors)}"
            
            return success_response(
                response_message,
                201,
                {
                    "product_id": str(product.id),
                    "variant_id": str(variant.id),
                    "images": uploaded_images,
                    "total_images": len(uploaded_images),
                    "errors": errors if errors else None
                }
            )
        except Exception as e:
            log_error(f"Failed to add images to variant {variant_id}", error=e)
            db.session.rollback()
            return error_response("Failed to upload images", 500)

    @staticmethod
    def remove_variant_image(product_id: str, variant_id: str, image_id: str) -> Response:
        """
        Remove an image from a product variant.
        
        Args:
            product_id: Product ID
            variant_id: Variant ID
            image_id: Media ID to remove
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                product_uuid = uuid.UUID(product_id)
                variant_uuid = uuid.UUID(variant_id)
                image_uuid = uuid.UUID(image_id)
            except ValueError:
                return error_response("Invalid ID format", 400)
            
            product = Product.query.get(product_uuid)
            if not product:
                return error_response("Product not found", 404)
            
            variant = ProductVariant.query.filter_by(id=variant_uuid, product_id=product_uuid).first()
            if not variant:
                return error_response("Variant not found", 404)
            
            # Check if image is associated with variant
            media = Media.query.get(image_uuid)
            if not media:
                return error_response("Image not found", 404)
            
            if media not in variant.images.all():
                return error_response("Image not associated with this variant", 404)
            
            # Remove association using relationship
            variant.images.remove(media)
            
            db.session.commit()
            
            log_event(f"Removed image {image_id} from variant {variant_id} by admin {current_user.id}")
            
            return success_response("Image removed successfully", 200)
        except Exception as e:
            log_error(f"Failed to remove image from variant {variant_id}", error=e)
            db.session.rollback()
            return error_response("Failed to remove image", 500)


class AdminMaterialController:
    """Controller for admin product material endpoints."""

    @staticmethod
    def create_material() -> Response:
        """
        Create a new product material.
        
        Requires admin authentication.
        """
        from app.schemas.materials import CreateMaterialRequest
        
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            payload = CreateMaterialRequest.model_validate(request.get_json())
            
            # Check if material with this name exists
            existing = ProductMaterial.query.filter_by(name=payload.name).first()
            if existing:
                return error_response("Material with this name already exists", 409)
            
            material = ProductMaterial()
            material.name = payload.name
            material.description = payload.description or ""
            
            db.session.add(material)
            db.session.commit()
            
            log_event(f"Material created: {material.id} by admin {current_user.id}")
            
            return success_response(
                "Material created successfully",
                201,
                {"material": material.to_dict()}
            )
        except Exception as e:
            log_error("Failed to create material", error=e)
            db.session.rollback()
            return error_response("Failed to create material", 500)

    @staticmethod
    def list_materials() -> Response:
        """
        List all product materials with optional search.
        
        Requires admin authentication.
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            # Get query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 50, type=int)
            search = request.args.get('search', type=str)
            
            # Build query
            query = ProductMaterial.query
            
            if search:
                query = query.filter(ProductMaterial.name.ilike(f'%{search}%'))
            
            query = query.order_by(ProductMaterial.name.asc())
            
            # Paginate
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            materials = [m.to_dict() for m in pagination.items]
            
            return success_response(
                "Materials retrieved successfully",
                200,
                {
                    "materials": materials,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages
                    }
                }
            )
        except Exception as e:
            log_error("Failed to list materials", error=e)
            return error_response("Failed to retrieve materials", 500)

    @staticmethod
    def get_material(material_id: str) -> Response:
        """
        Get a single product material by ID.
        
        Args:
            material_id: Material ID
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                material_uuid = uuid.UUID(material_id)
            except ValueError:
                return error_response("Invalid material ID format", 400)
            
            material = ProductMaterial.query.get(material_uuid)
            if not material:
                return error_response("Material not found", 404)
            
            return success_response(
                "Material retrieved successfully",
                200,
                {"material": material.to_dict(include_products=True)}
            )
        except Exception as e:
            log_error(f"Failed to get material {material_id}", error=e)
            return error_response("Failed to retrieve material", 500)

    @staticmethod
    def update_material(material_id: str) -> Response:
        """
        Update a product material.
        
        Args:
            material_id: Material ID
        """
        from app.schemas.materials import UpdateMaterialRequest
        
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                material_uuid = uuid.UUID(material_id)
            except ValueError:
                return error_response("Invalid material ID format", 400)
            
            material = ProductMaterial.query.get(material_uuid)
            if not material:
                return error_response("Material not found", 404)
            
            payload = UpdateMaterialRequest.model_validate(request.get_json())
            
            # Update fields
            if payload.name is not None:
                # Check name uniqueness
                existing = ProductMaterial.query.filter_by(name=payload.name).filter(ProductMaterial.id != material_uuid).first()
                if existing:
                    return error_response("Material with this name already exists", 409)
                material.name = payload.name
            
            if payload.description is not None:
                material.description = payload.description
            
            db.session.commit()
            
            log_event(f"Material updated: {material_id} by admin {current_user.id}")
            
            return success_response(
                "Material updated successfully",
                200,
                {"material": material.to_dict()}
            )
        except Exception as e:
            log_error(f"Failed to update material {material_id}", error=e)
            db.session.rollback()
            return error_response("Failed to update material", 500)

    @staticmethod
    def delete_material(material_id: str) -> Response:
        """
        Delete a product material.
        
        Only allowed if the material is not in use by any products.
        
        Args:
            material_id: Material ID
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                material_uuid = uuid.UUID(material_id)
            except ValueError:
                return error_response("Invalid material ID format", 400)
            
            material = ProductMaterial.query.get(material_uuid)
            if not material:
                return error_response("Material not found", 404)
            
            # Check if material is in use
            if material.usage_count > 0:
                return error_response(
                    f"Cannot delete material that is used by {material.usage_count} product(s). "
                    "Unlink products first.",
                    409
                )
            
            db.session.delete(material)
            db.session.commit()
            
            log_event(f"Material deleted: {material_id} by admin {current_user.id}")
            
            return success_response("Material deleted successfully", 200)
        except Exception as e:
            log_error(f"Failed to delete material {material_id}", error=e)
            db.session.rollback()
            return error_response("Failed to delete material", 500)
