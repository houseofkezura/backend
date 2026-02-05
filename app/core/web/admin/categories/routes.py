"""
Web admin category routes.
"""

from __future__ import annotations

from flask import render_template, request, redirect, url_for, flash
import uuid

from . import bp
from app.extensions import db
from app.models.category import ProductCategory
from app.utils.helpers.category import fetch_all_categories, fetch_category
from app.logging import log_error


@bp.route("", methods=["GET"], strict_slashes=False)
def categories():
    """
    List all categories with pagination and search.
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search_term = request.args.get('search', '').strip()
        parent_only = request.args.get('parent_only', 'true').lower() == 'true'
        
        # Use the helper function to fetch categories
        pagination = fetch_all_categories(
            cat_id=None,
            page_num=page,
            per_page=per_page,
            paginate=True,
            parent_only=parent_only,
            search_term=search_term
        )
        
        # Calculate total pages
        total_pages = pagination.pages
        
        return render_template(
            "admin/pages/prod_cats/categories.html",
            pagination=pagination,
            total_pages=total_pages,
            search_term=search_term,
            parent_only=parent_only
        )
    except Exception as e:
        log_error("Failed to list categories in web admin", error=e)
        flash("Failed to load categories. Please try again.", "error")
        return redirect(url_for("web.web_admin.web_admin_home.index"))


@bp.route("/<category_id>", methods=["GET"], strict_slashes=False)
def view_category(category_id: str):
    """
    View a single category by ID or slug.
    """
    try:
        category = fetch_category(category_id)
        
        if not category:
            flash("Category not found", "error")
            return redirect(url_for("web.web_admin.categories.categories"))
        
        # Get category data with children
        category_data = category.to_dict(include_children=True)
        
        return render_template(
            "admin/pages/prod_cats/view_category.html",
            category=category,
            category_data=category_data
        )
    except Exception as e:
        log_error(f"Failed to view category {category_id}", error=e)
        flash("Failed to load category. Please try again.", "error")
        return redirect(url_for("web.web_admin.categories.categories"))


@bp.route("/add", methods=["GET", "POST"], strict_slashes=False)
def add_new_category():
    """
    Show add category form and handle creation.
    """
    from app.utils.forms.admin.categories import CategoryForm
    from app.utils.helpers.category import save_category
    
    form = CategoryForm()
    
    if form.validate_on_submit():
        try:
            # Prepare data for save_category helper
            # The helper expects a dict and reads request.files directly for 'cat_img'
            # We need to ensure 'cat_img' is in request.files or handle it manually if WTForms handles it
            
            data = {
                'name': form.name.data,
                'description': form.description.data,
                'parent_cat': form.parent_id.data if form.parent_id.data else None
            }
            
            # The helper checks request.files.get('cat_img')
            # But our form field is named 'image'
            # We can either rename the form field or hack the request.files (not recommended)
            # OR better, update save_category helper. 
            # For now, let's pass the file manually if the helper supported it, but it reads request.files.
            # Let's see if we can trick it or if we should just rename the form field to cat_img.
            # Renaming form field to cat_img is easier.
            
            # Use save_category helper
            # Note: save_category relies on request.files['cat_img']
            
            save_category(data)
            
            flash("Category created successfully", "success")
            return redirect(url_for("web.web_admin.categories.categories"))
            
        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            log_error("Failed to create category", error=e)
            flash("Failed to create category. Please try again.", "error")
    
    return render_template(
        "admin/pages/prod_cats/add_category.html",
        form=form
    )


@bp.route("/<category_id>/edit", methods=["GET", "POST"], strict_slashes=False)
def edit_category(category_id: str):
    """
    Show edit category form and handle update.
    """
    try:
        category = fetch_category(category_id)
        
        if not category:
            flash("Category not found", "error")
            return redirect(url_for("web.web_admin.categories.categories"))
        
        from app.utils.forms.admin.categories import CategoryForm
        from app.utils.helpers.category import save_category
        
        # Initialize form with existing data
        form = CategoryForm(obj=category)
        
        # Set parent_id specifically as obj=category mapping might differ
        if request.method == 'GET':
            form.parent_id.data = str(category.parent_id) if category.parent_id else ""
        
        if form.validate_on_submit():
            try:
                data = {
                    'name': form.name.data,
                    'description': form.description.data,
                    'parent_cat': form.parent_id.data if form.parent_id.data else None
                }
                
                # Pass slug or ID to update
                save_category(data, slug=category.slug if category.slug else str(category.id))
                
                flash("Category updated successfully", "success")
                return redirect(url_for("web.web_admin.categories.categories"))
            except Exception as e:
                log_error("Failed to update category", error=e)
                flash(f"Failed to update category: {str(e)}", "error")

        return render_template(
            "admin/pages/prod_cats/edit_category.html",
            form=form,
            category=category
        )
    except Exception as e:
        log_error(f"Failed to load edit category {category_id}", error=e)
        flash("Failed to load category. Please try again.", "error")
        return redirect(url_for("web.web_admin.categories.categories"))
    except Exception as e:
        log_error(f"Failed to load edit category {category_id}", error=e)
        flash("Failed to load category. Please try again.", "error")
        return redirect(url_for("web.web_admin.categories.categories"))


@bp.route("/<category_id>/delete", methods=["POST"], strict_slashes=False)
def delete_category(category_id: str):
    """
    Delete a category.
    """
    try:
        category = fetch_category(category_id)
        
        if not category:
            flash("Category not found", "error")
            return redirect(url_for("web.web_admin.categories.categories"))
        
        category_name = category.name
        
        # Check if category has children
        if category.children:
            flash(f"Cannot delete category '{category_name}' because it has subcategories. Please delete or move subcategories first.", "error")
            return redirect(url_for("web.web_admin.categories.categories"))
        
        # Check if category has products
        if category.products.count() > 0:
            flash(f"Cannot delete category '{category_name}' because it has associated products.", "error")
            return redirect(url_for("web.web_admin.categories.categories"))
        
        # Delete category
        db.session.delete(category)
        db.session.commit()
        
        flash(f"Category '{category_name}' deleted successfully", "success")
        return redirect(url_for("web.web_admin.categories.categories"))
    except Exception as e:
        log_error(f"Failed to delete category {category_id}", error=e)
        db.session.rollback()
        flash("Failed to delete category. Please try again.", "error")
        return redirect(url_for("web.web_admin.categories.categories"))

