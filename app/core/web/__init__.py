"""
Web Blueprint registry.

Provides a minimal public web root with index page.
"""

from __future__ import annotations

from flask import Blueprint, redirect, url_for


def create_web_blueprint():
    """Create and return the web blueprint."""
    web_bp = Blueprint("web", __name__, url_prefix="/")

    @web_bp.route("/", methods=["GET"])
    def index():
        return redirect(url_for("api.index"))

    return web_bp