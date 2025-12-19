from __future__ import annotations

from flask import Blueprint, request

from .home import bp as home_bp
from .auth import bp as auth_bp
from app.utils.decorators.auth import roles_required_web, ADMIN_ALLOWED_ROLES


def create_web_admin_blueprint():
    """Create and return the web admin blueprint."""
    web_admin_bp = Blueprint("web_admin", __name__, url_prefix="/admin")

    # Register sub-blueprints
    web_admin_bp.register_blueprint(auth_bp)
    web_admin_bp.register_blueprint(home_bp)

    @web_admin_bp.before_request
    def _require_admin_access():
        """Protect all admin routes except the auth endpoints (login, callbacks)."""
        if not request.endpoint:
            return None

        # Allow any auth-related endpoints without guard
        if request.endpoint.startswith("web.web_admin.web_admin_auth"):
            return None

        # Enforce Clerk auth + RBAC
        guard = roles_required_web(*ADMIN_ALLOWED_ROLES)
        auth_result = guard(lambda: None)()  # type: ignore
        if auth_result is not None:
            return auth_result

        return None

    return web_admin_bp