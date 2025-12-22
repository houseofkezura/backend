from __future__ import annotations

from typing import Any

from flask import Blueprint, request, render_template

from app.logging import log_error
from app.extensions import db


def _rollback():
    """Rollback database session on error."""
    try:
        db.session.rollback()
    except Exception:
        pass


def _handle_unexpected(err: Exception):
    """Handle unexpected exceptions - show error page."""
    # For API routes, delegate to API handlers
    if request.path.startswith("/api"):
        from quas_utils.api import error_response
        _rollback()
        log_error("Unhandled exception", err, path=request.path)
        return error_response("internal server error", 500)
    
    _rollback()
    log_error("Unhandled exception", err, path=request.path)
    
    if request.path.startswith("/admin"):
        return render_template(
            "admin/base/errors_base.html",
            error_code=500,
            error_message="An unexpected error occurred. Please try again later."
        ), 500
    
    return render_template(
        "admin/base/errors_base.html",
        error_code=500,
        error_message="An unexpected error occurred"
    ), 500


def add_web_unexpected_err_handler(bp: Blueprint):
    """
    Register catch-all exception handler for web blueprints.
    This handler checks the path and delegates to API handlers for /api routes.
    Uses bp.register_error_handler like API handlers.
    """
    bp.register_error_handler(Exception, _handle_unexpected)
