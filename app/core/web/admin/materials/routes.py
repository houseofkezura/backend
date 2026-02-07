"""
Web admin product materials routes.
"""

from __future__ import annotations
from flask import render_template, request, redirect, url_for, flash, g
from . import bp
from app.models.product import ProductMaterial
from app.extensions import db
from app.logging import log_error, log_event

@bp.route("", methods=["GET"], strict_slashes=False)
def materials():
    """
    List all product materials with pagination.
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search_term = request.args.get('search', '').strip()
        
        query = ProductMaterial.query.order_by(ProductMaterial.name)
        
        if search_term:
            query = query.filter(ProductMaterial.name.ilike(f"%{search_term}%"))
        
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template(
            "admin/pages/materials/list.html",
            pagination=pagination,
            total_pages=pagination.pages,
            search_term=search_term
        )
    except Exception as e:
        log_error("Failed to list materials in web admin", error=e)
        flash("Failed to load materials. Please try again.", "error")
        return redirect(url_for("web.web_admin.web_admin_home.index"))


@bp.route("/add", methods=["GET", "POST"], strict_slashes=False)
def add_material():
    """
    Add a new product material.
    """
    if request.method == "POST":
        try:
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            
            if not name:
                flash("Material name is required.", "error")
                return render_template("admin/pages/materials/add.html")
            
            # Check for duplicate name
            existing = ProductMaterial.query.filter_by(name=name).first()
            if existing:
                flash(f"Material '{name}' already exists.", "error")
                return render_template("admin/pages/materials/add.html")
            
            material = ProductMaterial(name=name, description=description or None)
            db.session.add(material)
            db.session.commit()
            
            current_user = getattr(g, 'current_user', None)
            if current_user:
                log_event(f"Material created: {material.id} by admin {current_user.id}")
            
            flash(f"Material '{name}' created successfully.", "success")
            return redirect(url_for("web.web_admin.materials.materials"))
            
        except Exception as e:
            db.session.rollback()
            log_error("Failed to create material", error=e)
            flash("Failed to create material. Please try again.", "error")
    
    return render_template("admin/pages/materials/add.html")


@bp.route("/<material_id>/edit", methods=["GET", "POST"], strict_slashes=False)
def edit_material(material_id: str):
    """
    Edit a product material.
    """
    try:
        material = ProductMaterial.query.get(material_id)
        if not material:
            flash("Material not found.", "error")
            return redirect(url_for("web.web_admin.materials.materials"))
        
        if request.method == "POST":
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            
            if not name:
                flash("Material name is required.", "error")
                return render_template("admin/pages/materials/edit.html", material=material)
            
            # Check for duplicate name (excluding current)
            existing = ProductMaterial.query.filter(
                ProductMaterial.name == name,
                ProductMaterial.id != material.id
            ).first()
            if existing:
                flash(f"Material '{name}' already exists.", "error")
                return render_template("admin/pages/materials/edit.html", material=material)
            
            material.name = name
            material.description = description or None
            db.session.commit()
            
            flash(f"Material '{name}' updated successfully.", "success")
            return redirect(url_for("web.web_admin.materials.materials"))
        
        return render_template("admin/pages/materials/edit.html", material=material)
        
    except Exception as e:
        db.session.rollback()
        log_error(f"Failed to edit material {material_id}", error=e)
        flash("Failed to update material. Please try again.", "error")
        return redirect(url_for("web.web_admin.materials.materials"))


@bp.route("/<material_id>/delete", methods=["POST"], strict_slashes=False)
def delete_material(material_id: str):
    """
    Delete a product material.
    """
    try:
        material = ProductMaterial.query.get(material_id)
        if not material:
            flash("Material not found.", "error")
            return redirect(url_for("web.web_admin.materials.materials"))
        
        if material.usage_count > 0:
            flash(f"Cannot delete '{material.name}' - it is used by {material.usage_count} product(s).", "error")
            return redirect(url_for("web.web_admin.materials.materials"))
        
        name = material.name
        db.session.delete(material)
        db.session.commit()
        
        flash(f"Material '{name}' deleted successfully.", "success")
        
    except Exception as e:
        db.session.rollback()
        log_error(f"Failed to delete material {material_id}", error=e)
        flash("Failed to delete material. Please try again.", "error")
    
    return redirect(url_for("web.web_admin.materials.materials"))
