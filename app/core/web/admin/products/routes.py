"""
Web admin product routes.
"""

from __future__ import annotations

from flask import render_template, request, redirect, url_for, flash, g
from sqlalchemy import or_
from slugify import slugify
import uuid
import random
import string

from . import bp
from app.extensions import db
from app.models.product import Product, ProductVariant, Inventory
from app.models.category import ProductCategory
from app.utils.forms.admin.products import ProductForm
from app.utils.forms.admin.products import generate_category_field
from app.logging import log_error, log_event


def _get_category_code(category_name: str) -> str:
    """Map product category to 2-letter code for SKU generation."""
    category_map = {
        "Wigs": "WG",
        "Bundles": "BD",
        "Hair Care": "HC",
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


@bp.route("", methods=["GET"], strict_slashes=False)
def products():
    """
    List all products with pagination and search.
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search_term = request.args.get('search', '').strip()
        category = request.args.get('category', type=str)
        status = request.args.get('status', type=str)
        
        # Build query
        query = Product.query
        
        # Apply search filter
        if search_term:
            query = Product.add_search_filters(query, search_term)
        
        # Apply category filter
        if category:
            query = query.filter(Product.category == category)
        
        # Apply status filter
        if status:
            query = query.filter(Product.launch_status == status)
        
        # Order by created_at desc
        query = query.order_by(Product.created_at.desc())
        
        # Paginate
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Convert products to dict with images for template
        products_with_images = []
        for product in pagination.items:
            product_dict = product.to_dict(include_variants=False)
            products_with_images.append(product_dict)
        
        # Create a custom pagination-like object with products that have image data
        class PaginationWrapper:
            def __init__(self, pagination, items):
                self.items = items
                self.page = pagination.page
                self.per_page = pagination.per_page
                self.total = pagination.total
                self.pages = pagination.pages
                self.has_prev = pagination.has_prev
                self.has_next = pagination.has_next
                self.prev_num = pagination.prev_num
                self.next_num = pagination.next_num
        
        pagination_wrapper = PaginationWrapper(pagination, products_with_images)
        
        # Calculate total pages
        total_pages = pagination.pages
        
        return render_template(
            "admin/pages/products/products.html",
            pagination=pagination_wrapper,
            total_pages=total_pages,
            search_term=search_term,
            category=category,
            status=status
        )
    except Exception as e:
        log_error("Failed to list products in web admin", error=e)
        flash("Failed to load products. Please try again.", "error")
        return redirect(url_for("web.web_admin.web_admin_home.index"))


@bp.route("/<product_id>", methods=["GET"], strict_slashes=False)
def view_product(product_id: str):
    """
    View a single product by ID.
    """
    try:
        try:
            product_uuid = uuid.UUID(product_id)
        except ValueError:
            flash("Invalid product ID", "error")
            return redirect(url_for("web.web_admin.products.products"))
        
        product = Product.query.get(product_uuid)
        
        if not product:
            flash("Product not found", "error")
            return redirect(url_for("web.web_admin.products.products"))
        
        # Get product data with variants
        product_data = product.to_dict(include_variants=True)
        
        return render_template(
            "admin/pages/products/view_product.html",
            product=product,
            product_data=product_data
        )
    except Exception as e:
        log_error(f"Failed to view product {product_id}", error=e)
        flash("Failed to load product. Please try again.", "error")
        return redirect(url_for("web.web_admin.products.products"))


@bp.route("/add", methods=["GET", "POST"], strict_slashes=False)
def add_new_product():
    """
    Add a new product - GET shows form, POST processes submission.
    """
    form = ProductForm()
    
    # Generate category field HTML
    category_field = generate_category_field(format='checkbox')
    parent_cat_field = generate_category_field(format='select')
    
    if request.method == "POST":
        if form.validate_on_submit():
            try:
                # Get category model
                category_id = form.category_id.data
                try:
                    category_uuid = uuid.UUID(category_id) if category_id else None
                    category_model = ProductCategory.query.get(category_uuid) if category_uuid else None
                except (ValueError, TypeError):
                    category_model = None
                
                if not category_model:
                    flash("Invalid category selected", "error")
                    return render_template(
                        "admin/pages/products/add_product.html",
                        form=form,
                        category_field=category_field,
                        parent_cat_field=parent_cat_field
                    )
                
                category_name = category_model.name
                
                # Generate slug if not provided
                product_slug = form.slug.data or slugify(form.name.data)
                
                # Check if slug exists
                existing = Product.query.filter_by(slug=product_slug).first()
                if existing:
                    form.slug.errors.append("Product with this slug already exists")
                    return render_template(
                        "admin/pages/products/add_product.html",
                        form=form,
                        category_field=category_field,
                        parent_cat_field=parent_cat_field
                    )
                
                # Generate SKU if not provided
                product_sku = form.sku.data
                if not product_sku:
                    max_attempts = 100
                    for _ in range(max_attempts):
                        product_sku = _generate_sku(category_name)
                        if not Product.query.filter_by(sku=product_sku).first():
                            break
                    else:
                        # Fallback
                        category_code = _get_category_code(category_name)
                        product_sku = f"KZ-{category_code}-{str(uuid.uuid4())[:4].upper()}"
                else:
                    # Check if provided SKU exists
                    existing_sku = Product.query.filter_by(sku=product_sku).first()
                    if existing_sku:
                        form.sku.errors.append("Product with this SKU already exists")
                        return render_template(
                            "admin/pages/products/add_product.html",
                            form=form,
                            category_field=category_field,
                            parent_cat_field=parent_cat_field
                        )
                
                # Create product
                product = Product()
                product.name = form.name.data
                product.sku = product_sku
                product.slug = product_slug
                product.description = form.description.data or ""
                product.category = category_name
                product.care = form.care.data or ""
                product.details = form.details.data or ""
                product.material = form.material.data or ""
                product.meta_title = form.meta_title.data
                product.meta_description = form.meta_description.data
                product.meta_keywords = form.meta_keywords.data
                product.launch_status = form.launch_status.data or "In-Stock"
                
                db.session.add(product)
                db.session.flush()
                
                # Link category relationship
                if category_model:
                    product.categories.append(category_model)
                
                # Handle additional categories if selected
                if form.categories.data:
                    for cat_id in form.categories.data:
                        try:
                            cat_uuid = uuid.UUID(cat_id)
                            additional_cat = ProductCategory.query.get(cat_uuid)
                            if additional_cat and additional_cat not in product.categories:
                                product.categories.append(additional_cat)
                        except (ValueError, TypeError):
                            continue
                
                db.session.commit()
                
                current_user = getattr(g, 'current_user', None)
                if current_user:
                    log_event(f"Product created: {product.id} by admin {current_user.id}")
                
                flash(f"Product '{product.name}' created successfully", "success")
                return redirect(url_for("web.web_admin.products.view_product", product_id=product.id))
                
            except Exception as e:
                log_error("Failed to create product", error=e)
                db.session.rollback()
                flash("Failed to create product. Please try again.", "error")
        else:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{getattr(form, field).label.text}: {error}", "error")
    
    return render_template(
        "admin/pages/products/add_product.html",
        form=form,
        category_field=category_field,
        parent_cat_field=parent_cat_field
    )


@bp.route("/<product_id>/edit", methods=["GET", "POST"], strict_slashes=False)
def edit_product(product_id: str):
    """
    Edit a product - GET shows form, POST processes submission.
    """
    try:
        try:
            product_uuid = uuid.UUID(product_id)
        except ValueError:
            flash("Invalid product ID", "error")
            return redirect(url_for("web.web_admin.products.products"))
        
        product = Product.query.get(product_uuid)
        
        if not product:
            flash("Product not found", "error")
            return redirect(url_for("web.web_admin.products.products"))
        
        # Initialize form with product data
        form = ProductForm(
            name=product.name,
            sku=product.sku,
            slug=product.slug,
            description=product.description or "",
            care=product.care or "",
            details=product.details or "",
            material=product.material or "",
            meta_title=product.meta_title or "",
            meta_description=product.meta_description or "",
            meta_keywords=product.meta_keywords or "",
            launch_status=product.launch_status or "In-Stock"
        )
        
        # Set category_id from product's categories relationship
        if product.categories:
            form.category_id.data = str(product.categories[0].id)
        
        # Set selected categories for multi-select
        if product.categories:
            form.categories.data = [str(cat.id) for cat in product.categories]
        
        # Generate category field HTML with selected categories
        selected_cats = list(product.categories) if product.categories else []
        category_field = generate_category_field(format='checkbox', sel_cats=selected_cats)
        parent_cat_field = generate_category_field(format='select')
        
        if request.method == "POST":
            # Store product_id for validation
            form.product_id = product.id
            
            if form.validate_on_submit():
                try:
                    # Get category model
                    category_id = form.category_id.data
                    try:
                        category_uuid = uuid.UUID(category_id) if category_id else None
                        category_model = ProductCategory.query.get(category_uuid) if category_uuid else None
                    except (ValueError, TypeError):
                        category_model = None
                    
                    if not category_model:
                        flash("Invalid category selected", "error")
                        return render_template(
                            "admin/pages/products/edit_product.html",
                            form=form,
                            product=product,
                            category_field=category_field,
                            parent_cat_field=parent_cat_field
                        )
                    
                    category_name = category_model.name
                    
                    # Update product fields
                    product.name = form.name.data
                    
                    # Update SKU if changed
                    if form.sku.data and form.sku.data != product.sku:
                        existing_sku = Product.query.filter_by(sku=form.sku.data).filter(Product.id != product_uuid).first()
                        if existing_sku:
                            form.sku.errors.append("SKU already in use")
                            return render_template(
                                "admin/pages/products/edit_product.html",
                                form=form,
                                product=product,
                                category_field=category_field,
                                parent_cat_field=parent_cat_field
                            )
                        product.sku = form.sku.data
                    
                    # Update slug if changed
                    if form.slug.data and form.slug.data != product.slug:
                        existing = Product.query.filter_by(slug=form.slug.data).filter(Product.id != product_uuid).first()
                        if existing:
                            form.slug.errors.append("Slug already in use")
                            return render_template(
                                "admin/pages/products/edit_product.html",
                                form=form,
                                product=product,
                                category_field=category_field,
                                parent_cat_field=parent_cat_field
                            )
                        product.slug = form.slug.data
                    elif not form.slug.data:
                        # Auto-generate if blank
                        product.slug = slugify(form.name.data)
                    
                    product.description = form.description.data or ""
                    product.category = category_name
                    product.care = form.care.data or ""
                    product.details = form.details.data or ""
                    product.material = form.material.data or ""
                    product.meta_title = form.meta_title.data
                    product.meta_description = form.meta_description.data
                    product.meta_keywords = form.meta_keywords.data
                    if form.launch_status.data:
                        product.launch_status = form.launch_status.data
                    
                    # Update category relationships
                    product.categories = []
                    if category_model:
                        product.categories.append(category_model)
                    
                    # Handle additional categories if selected
                    if form.categories.data:
                        for cat_id in form.categories.data:
                            try:
                                cat_uuid = uuid.UUID(cat_id)
                                additional_cat = ProductCategory.query.get(cat_uuid)
                                if additional_cat and additional_cat not in product.categories:
                                    product.categories.append(additional_cat)
                            except (ValueError, TypeError):
                                continue
                    
                    db.session.commit()
                    
                    current_user = getattr(g, 'current_user', None)
                    if current_user:
                        log_event(f"Product updated: {product_id} by admin {current_user.id}")
                    
                    flash(f"Product '{product.name}' updated successfully", "success")
                    return redirect(url_for("web.web_admin.products.view_product", product_id=product.id))
                    
                except Exception as e:
                    log_error(f"Failed to update product {product_id}", error=e)
                    db.session.rollback()
                    flash("Failed to update product. Please try again.", "error")
            else:
                # Form validation failed
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f"{getattr(form, field).label.text}: {error}", "error")
        
        return render_template(
            "admin/pages/products/edit_product.html",
            form=form,
            product=product,
            category_field=category_field,
            parent_cat_field=parent_cat_field
        )
    except Exception as e:
        log_error(f"Failed to load edit product {product_id}", error=e)
        flash("Failed to load product. Please try again.", "error")
        return redirect(url_for("web.web_admin.products.products"))


@bp.route("/<product_id>/delete", methods=["POST"], strict_slashes=False)
def delete_product(product_id: str):
    """
    Delete a product.
    """
    try:
        try:
            product_uuid = uuid.UUID(product_id)
        except ValueError:
            flash("Invalid product ID", "error")
            return redirect(url_for("web.web_admin.products.products"))
        
        product = Product.query.get(product_uuid)
        
        if not product:
            flash("Product not found", "error")
            return redirect(url_for("web.web_admin.products.products"))
        
        product_name = product.name
        
        # Delete product (cascade will handle variants and inventory)
        db.session.delete(product)
        db.session.commit()
        
        flash(f"Product '{product_name}' deleted successfully", "success")
        return redirect(url_for("web.web_admin.products.products"))
    except Exception as e:
        log_error(f"Failed to delete product {product_id}", error=e)
        db.session.rollback()
        flash("Failed to delete product. Please try again.", "error")
        return redirect(url_for("web.web_admin.products.products"))
