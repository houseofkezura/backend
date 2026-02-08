from __future__ import annotations

from flask import render_template, request, flash, redirect, url_for
from . import bp
from app.models.user import AppUser
from app.models.order import Order
from sqlalchemy import desc
from app.logging import log_error

@bp.route("/", methods=["GET"])
def users():
    """List all registered users with search and pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search_term = request.args.get('search', '').strip()
        
        query = AppUser.query.order_by(AppUser.date_joined.desc())
        
        if search_term:
            query = AppUser.add_search_filters(query, search_term)
            
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template(
            "admin/pages/users/list.html",
            pagination=pagination,
            total_pages=pagination.pages,
            search_term=search_term
        )
    except Exception as e:
        log_error("Failed to list users in admin", error=e)
        flash("An error occurred while loading users.", "error")
        return redirect(url_for("web.web_admin.web_admin_home.index"))

@bp.route("/<user_id>", methods=["GET"])
def view_user(user_id: str):
    """View details of a specific user."""
    try:
        user = AppUser.query.get(user_id)
        if not user:
            flash("User not found.", "error")
            return redirect(url_for("web.web_admin.users.users"))
            
        return render_template(
            "admin/pages/users/view.html",
            user=user,
            Order=Order,
            desc=desc
        )
    except Exception as e:
        log_error(f"Failed to view user {user_id}", error=e)
        flash("An error occurred while loading the user details.", "error")
        return redirect(url_for("web.web_admin.users.users"))
