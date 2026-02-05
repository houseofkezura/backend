"""
Web admin order routes.
"""

from __future__ import annotations
from flask import render_template, request, redirect, url_for, flash
from . import bp
from app.utils.helpers.order import fetch_all_orders, fetch_order
from app.logging import log_error
from app.enums.orders import OrderStatus

@bp.route("", methods=["GET"], strict_slashes=False)
def orders():
    """
    List all orders with pagination and filtering.
    """
    try:
        # Get query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search_term = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        
        # Fetch orders
        pagination = fetch_all_orders(
            page_num=page,
            per_page=per_page,
            paginate=True,
            status=status if status else None,
            search_term=search_term
        )
        
        total_pages = pagination.pages
        
        return render_template(
            "admin/pages/orders/list.html",
            pagination=pagination,
            total_pages=total_pages,
            search_term=search_term,
            current_status=status,
            OrderStatus=OrderStatus
        )
    except Exception as e:
        log_error("Failed to list orders in web admin", error=e)
        flash("Failed to load orders. Please try again.", "error")
        return redirect(url_for("web.web_admin.web_admin_home.index"))


@bp.route("/<order_id>", methods=["GET"], strict_slashes=False)
def view_order(order_id: str):
    """
    View a single order details.
    """
    try:
        order = fetch_order(order_id)
        
        if not order:
            flash("Order not found", "error")
            return redirect(url_for("web.web_admin.orders.orders"))
        
        return render_template(
            "admin/pages/orders/view.html",
            order=order,
            OrderStatus=OrderStatus
        )
    except Exception as e:
        log_error(f"Failed to view order {order_id}", error=e)
        flash("Failed to load order. Please try again.", "error")
        return redirect(url_for("web.web_admin.orders.orders"))
