from __future__ import annotations

from flask import render_template

from . import bp
from app.extensions import db
from app.models.product import Product
from app.models.user import AppUser


@bp.route("/", methods=["GET"])
def index():
    """
    Admin dashboard (fallback UI).

    Uses direct DB counts to avoid BuildError/Undefined errors in templates.
    Recent lists are empty until the corresponding pages are implemented.
    """
    stats = {
        "total_products": Product.query.count(),
        "total_categories": db.session.query(Product.category).distinct().count(),
        "total_tags": 0,  # No tag model yet
        "total_users": AppUser.query.count(),
        "recent_orders": [],
        "recent_products": [],
    }

    return render_template("admin/pages/dashboard/dashboard.html", stats=stats)