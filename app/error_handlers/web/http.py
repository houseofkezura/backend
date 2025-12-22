from __future__ import annotations

from typing import Any

from flask import Blueprint, request, redirect, url_for, render_template
from werkzeug.exceptions import HTTPException, NotFound, MethodNotAllowed, Unauthorized, Forbidden

from app.logging import log_error


def _handle_http_exception(err: HTTPException):
    """Handle general HTTP exceptions - redirect to appropriate page or show error."""
    # For API routes, delegate to API handlers
    if request.path.startswith("/api"):
        from quas_utils.api import error_response
        status = err.code or 500
        description = err.description or err.name
        return error_response(description, status)
    
    log_error("HTTP exception", err, path=request.path)
    status = err.code or 500
    
    # For admin routes, redirect auth errors to login
    if request.path.startswith("/admin"):
        if status in (401, 403):
            return redirect(url_for("web.web_admin.web_admin_auth.login", next=request.url, _external=False))
        if status == 404:
            return render_template("admin/base/errors_base.html", error_code=404, error_message="Page not found"), 404
    
    # For other web routes, show generic error
    return render_template("admin/base/errors_base.html", error_code=status, error_message=err.description or err.name), status


def _handle_not_found(err: NotFound):
    """Handle 404 errors - show not found page."""
    # For API routes, delegate to API handlers
    if request.path.startswith("/api"):
        from quas_utils.api import error_response
        return error_response("Resource not found", 404)
    
    log_error("Not found", err, path=request.path)
    
    if request.path.startswith("/admin"):
        return render_template("admin/base/errors_base.html", error_code=404, error_message="Page not found"), 404
    
    return render_template("admin/base/errors_base.html", error_code=404, error_message="Page not found"), 404


def _handle_method_not_allowed(err: MethodNotAllowed):
    """Handle 405 errors - show method not allowed page."""
    # For API routes, delegate to API handlers
    if request.path.startswith("/api"):
        from quas_utils.api import error_response
        return error_response("Method not allowed", 405)
    
    log_error("Method not allowed", err, path=request.path)
    
    if request.path.startswith("/admin"):
        return render_template("admin/base/errors_base.html", error_code=405, error_message="Method not allowed"), 405
    
    return render_template("admin/base/errors_base.html", error_code=405, error_message="Method not allowed"), 405


def _handle_unauthorized(err: Unauthorized):
    """Handle 401 errors - redirect to login for admin routes."""
    # For API routes, delegate to API handlers
    if request.path.startswith("/api"):
        from quas_utils.api import error_response
        return error_response("Unauthorized", 401)
    
    log_error("Unauthorized", err, path=request.path)
    
    if request.path.startswith("/admin"):
        return redirect(url_for("web.web_admin.web_admin_auth.login", next=request.url, _external=False))
    
    return render_template("admin/base/errors_base.html", error_code=401, error_message="Unauthorized"), 401


def _handle_forbidden(err: Forbidden):
    """Handle 403 errors - redirect to login for admin routes."""
    # For API routes, delegate to API handlers
    if request.path.startswith("/api"):
        from quas_utils.api import error_response
        return error_response("Access forbidden", 403)
    
    log_error("Forbidden", err, path=request.path)
    
    if request.path.startswith("/admin"):
        return redirect(url_for("web.web_admin.web_admin_auth.login", next=request.url, _external=False))
    
    return render_template("admin/base/errors_base.html", error_code=403, error_message="Access forbidden"), 403


def add_web_http_err_handlers(bp: Blueprint):
    """
    Register HTTP error handlers for web blueprints.
    These handlers check the path and delegate to API handlers for /api routes.
    Uses bp.app_errorhandler like API handlers.
    """
    bp.app_errorhandler(HTTPException)(_handle_http_exception)
    bp.app_errorhandler(NotFound)(_handle_not_found)
    bp.app_errorhandler(MethodNotAllowed)(_handle_method_not_allowed)
    bp.app_errorhandler(Unauthorized)(_handle_unauthorized)
    bp.app_errorhandler(Forbidden)(_handle_forbidden)
