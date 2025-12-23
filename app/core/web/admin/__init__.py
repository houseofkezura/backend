from __future__ import annotations

from flask import Blueprint, request, redirect, url_for

from .home import bp as home_bp
from .auth import bp as auth_bp
from .settings import bp as settings_bp
from .products import bp as products_bp
from .categories import bp as categories_bp
from app.utils.decorators.auth import roles_required_web, ADMIN_ALLOWED_ROLES


def create_web_admin_blueprint():
    """Create and return the web admin blueprint."""
    web_admin_bp = Blueprint("web_admin", __name__, url_prefix="/admin")

    # Register sub-blueprints
    web_admin_bp.register_blueprint(auth_bp)
    web_admin_bp.register_blueprint(home_bp)
    web_admin_bp.register_blueprint(settings_bp)
    web_admin_bp.register_blueprint(products_bp)
    web_admin_bp.register_blueprint(categories_bp)

    @web_admin_bp.before_request
    def _require_admin_access():
        """Protect all admin routes except the auth endpoints (login, callbacks)."""
        if not request.endpoint:
            return None

        # Allow any auth-related endpoints without guard
        if request.endpoint.startswith("web.web_admin.web_admin_auth"):
            return None

        # Enforce Clerk auth + RBAC
        # Wrap in try/except to prevent exceptions from bubbling to API error handlers
        try:
            guard = roles_required_web(*ADMIN_ALLOWED_ROLES)
            auth_result = guard(lambda: None)()  # type: ignore
            if auth_result is not None:
                return auth_result
        except Exception:
            # If any exception occurs during auth, redirect to login
            # This prevents API error handlers from catching web admin errors
            return redirect(url_for("web.web_admin.web_admin_auth.login", next=request.url, _external=False))

        return None

    return web_admin_bp