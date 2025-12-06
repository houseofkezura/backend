"""
API Blueprint registry.

Provides a minimal public API root with health and version endpoints.
Also registers versioned sub-blueprints, e.g., `v1`.
"""

from __future__ import annotations

from flask import Blueprint, current_app, render_template

from app.utils.helpers.api_response import success_response


def create_api_blueprint():
    """Create and return the API blueprint."""
    api_bp = Blueprint("api", __name__, url_prefix="/api")

    @api_bp.route("/", methods=["GET"])
    def index():
        return render_template("api/index.html")


    @api_bp.get("/health")
    def api_health():
        """Return a basic liveness response for the API root."""
        return success_response("success", 200)


    @api_bp.get("/version")
    def api_version():
        """Return service metadata for the API root."""
        data = {
            "name": current_app.config.get("PROJECT_NAME", "Quas API"),
            "version": current_app.config.get("PROJECT_VERSION", "0.1.0"),
            "env": current_app.config.get("ENV")
        }
        return success_response("ok", 200, data)

    return api_bp