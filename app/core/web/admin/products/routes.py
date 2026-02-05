"""
Web admin product routes.
"""

from __future__ import annotations

from flask import render_template, request, redirect, url_for, flash, g

from . import bp
from app.extensions import db
from app.models.product import Product
from app.utils.forms.admin.products import ProductForm, generate_category_field
from app.utils.helpers.product import fetch_product, save_product
from app.logging import log_error, log_event


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


@bp.route("/<identifier>", methods=["GET"], strict_slashes=False)
def view_product(identifier: str):
    """
    View a single product by ID.
    """
    try:
        product = fetch_product(identifier)
        
        if not product:
            flash("Product not found", "error")
            return redirect(url_for("web.web_admin.products.products"))
        
        # Get product data with variants
        product_data = product.to_dict(include_variants=True)
        
        return render_template(
            "admin/pages/products/product_details.html",
            product=product,
            product_data=product_data
        )
    except Exception as e:
        log_error(f"Failed to view product {identifier}", error=e)
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
                # Get form data - handle both single and multi-value fields
                form_data = {}
                for key in request.form:
                    values = request.form.getlist(key)
                    if len(values) == 1:
                        form_data[key] = values[0]
                    else:
                        form_data[key] = values
                
                product = save_product(form_data, files=request.files)
                
                current_user = getattr(g, 'current_user', None)
                if current_user:
                    log_event(f"Product created: {product.id} by admin {current_user.id}")
                
                flash(f"Product '{product.name}' created successfully", "success")
                return redirect(url_for("web.web_admin.products.view_product", identifier=product.id))
                
            except ValueError as e:
                flash(str(e), "error")
            except Exception as e:
                log_error("Failed to create product", error=e)
                flash("Failed to create product. Please try again.", "error")
        else:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{getattr(form, field).label.text}: {error}", "error")
    
    return render_template(
        "admin/pages/products/new_products.html",
        form=form,
        category_field=category_field,
        parent_cat_field=parent_cat_field
    )


@bp.route("/<identifier>/edit", methods=["GET", "POST"], strict_slashes=False)
def edit_product(identifier: str):
    """
    Edit a product - GET shows form, POST processes submission.
    """
    try:
        product = fetch_product(identifier)
        
        if not product:
            flash("Product not found", "error")
            return redirect(url_for("web.web_admin.products.products"))
        
        # Initialize form with product data
        form = ProductForm(
            name=product.name,
            slug=product.slug,
            description=product.description or "",
            care=product.care or "",
            details=product.details or "",
            material=str(product.material_id) if product.material_id else "",
            colors=product.product_metadata.get('colors', '') if product.product_metadata else ''
        )
        
        # Set primary category from product's categories relationship
        if product.categories:
            form.product_category.data = str(product.categories[0].id)
        
        # Generate category field HTML with selected categories
        selected_cats = list(product.categories) if product.categories else []
        category_field = generate_category_field(format='checkbox', sel_cats=selected_cats)
        parent_cat_field = generate_category_field(format='select')
        
        if request.method == "POST":
            if form.validate_on_submit():
                try:
                    # Get form data - handle both single and multi-value fields
                    form_data = {}
                    for key in request.form:
                        values = request.form.getlist(key)
                        if len(values) == 1:
                            form_data[key] = values[0]
                        else:
                            form_data[key] = values
                    
                    # Update product
                    product = save_product(form_data, product=product, files=request.files)
                    
                    current_user = getattr(g, 'current_user', None)
                    if current_user:
                        log_event(f"Product updated: {product.id} by admin {current_user.id}")
                    
                    flash(f"Product '{product.name}' updated successfully", "success")
                    return redirect(url_for("web.web_admin.products.view_product", identifier=product.id))
                    
                except ValueError as e:
                    flash(str(e), "error")
                except Exception as e:
                    log_error(f"Failed to update product {product.id}", error=e)
                    flash("Failed to update product. Please try again.", "error")
            else:
                # Form validation failed
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f"{getattr(form, field).label.text}: {error}", "error")
        
        # Serialize existing variants for JavaScript
        existing_variants_data = []
        if product.variants:
            for variant in product.variants:
                # Build variant name from attributes
                variant_name_parts = []
                if variant.attributes:
                    for key, value in variant.attributes.items():
                        if not key.endswith('_visual') and value:
                            variant_name_parts.append(str(value))
                variant_name = ' / '.join(variant_name_parts) if variant_name_parts else variant.sku
                
                variant_dict = {
                    'name': variant_name,
                    'sku': variant.sku,
                    'price_ngn': float(variant.price_ngn),
                    'price_usd': float(variant.price_usd) if variant.price_usd else 0,
                    'quantity': variant.inventory.quantity if variant.inventory else 0,
                    'low_stock_threshold': variant.inventory.low_stock_threshold if variant.inventory else 5,
                    'weight_g': variant.weight_g or 0,
                    'attributes': variant.attributes or {}
                }
                existing_variants_data.append(variant_dict)
        
        return render_template(
            "admin/pages/products/edit_product.html",
            form=form,
            product=product,
            category_field=category_field,
            parent_cat_field=parent_cat_field,
            existing_variants=existing_variants_data
        )
    except Exception as e:
        log_error(f"Failed to load edit product {identifier}", error=e)
        flash("Failed to load product. Please try again.", "error")
        return redirect(url_for("web.web_admin.products.products"))


@bp.route("/<identifier>/delete", methods=["POST"], strict_slashes=False)
def delete_product(identifier: str):
    """
    Delete a product.
    """
    try:
        product = fetch_product(identifier)
        
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
        log_error(f"Failed to delete product {identifier}", error=e)
        db.session.rollback()
        flash("Failed to delete product. Please try again.", "error")
        return redirect(url_for("web.web_admin.products.products"))
