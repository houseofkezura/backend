"""
Web admin product routes.
"""

from __future__ import annotations

from flask import render_template, request, redirect, url_for, flash
from sqlalchemy import or_

from . import bp
from app.extensions import db
from app.models.product import Product
from app.logging import log_error


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
        import uuid
        try:
            product_uuid = uuid.UUID(product_id)
        except ValueError:
            flash("Invalid product ID", "error")
            return redirect(url_for("web.web_admin.web_admin_products.products"))
        
        product = Product.query.get(product_uuid)
        
        if not product:
            flash("Product not found", "error")
            return redirect(url_for("web.web_admin.web_admin_products.products"))
        
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
        return redirect(url_for("web.web_admin.web_admin_products.products"))


@bp.route("/add", methods=["GET"], strict_slashes=False)
def add_new_product():
    """
    Show add product form.
    """
    return render_template("admin/pages/products/add_product.html")


@bp.route("/<product_id>/edit", methods=["GET"], strict_slashes=False)
def edit_product(product_id: str):
    """
    Show edit product form.
    """
    try:
        import uuid
        try:
            product_uuid = uuid.UUID(product_id)
        except ValueError:
            flash("Invalid product ID", "error")
            return redirect(url_for("web.web_admin.web_admin_products.products"))
        
        product = Product.query.get(product_uuid)
        
        if not product:
            flash("Product not found", "error")
            return redirect(url_for("web.web_admin.web_admin_products.products"))
        
        product_data = product.to_dict(include_variants=True)
        
        return render_template(
            "admin/pages/products/edit_product.html",
            product=product,
            product_data=product_data
        )
    except Exception as e:
        log_error(f"Failed to load edit product {product_id}", error=e)
        flash("Failed to load product. Please try again.", "error")
        return redirect(url_for("web.web_admin.web_admin_products.products"))


@bp.route("/<product_id>/delete", methods=["POST"], strict_slashes=False)
def delete_product(product_id: str):
    """
    Delete a product.
    """
    try:
        import uuid
        try:
            product_uuid = uuid.UUID(product_id)
        except ValueError:
            flash("Invalid product ID", "error")
            return redirect(url_for("web.web_admin.web_admin_products.products"))
        
        product = Product.query.get(product_uuid)
        
        if not product:
            flash("Product not found", "error")
            return redirect(url_for("web.web_admin.web_admin_products.products"))
        
        product_name = product.name
        
        # Delete product (cascade will handle variants and inventory)
        db.session.delete(product)
        db.session.commit()
        
        flash(f"Product '{product_name}' deleted successfully", "success")
        return redirect(url_for("web.web_admin.web_admin_products.products"))
    except Exception as e:
        log_error(f"Failed to delete product {product_id}", error=e)
        db.session.rollback()
        flash("Failed to delete product. Please try again.", "error")
        return redirect(url_for("web.web_admin.web_admin_products.products"))

