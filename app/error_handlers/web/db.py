from __future__ import annotations

from typing import Any

from flask import Blueprint, request, render_template, redirect, url_for
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    InvalidRequestError,
    OperationalError,
    DatabaseError,
)

from app.logging import log_error
from app.extensions import db


def _rollback():
    """Rollback database session on error."""
    try:
        db.session.rollback()
    except Exception:
        pass


def _handle_integrity(err: IntegrityError):
    """Handle database integrity errors."""
    # For API routes, delegate to API handlers
    if request.path.startswith("/api"):
        from quas_utils.api import error_response
        _rollback()
        log_error("Integrity error", err, path=request.path)
        return error_response("conflict with existing data", 409)
    
    _rollback()
    log_error("Database integrity error", err, path=request.path)
    
    if request.path.startswith("/admin"):
        return render_template(
            "admin/base/errors_base.html",
            error_code=400,
            error_message="Database integrity error. Please check your input."
        ), 400
    
    return render_template(
        "admin/base/errors_base.html",
        error_code=400,
        error_message="Database integrity error"
    ), 400


def _handle_data(err: DataError):
    """Handle data errors."""
    # For API routes, delegate to API handlers
    if request.path.startswith("/api"):
        from quas_utils.api import error_response
        _rollback()
        log_error("Invalid data", err, path=request.path)
        return error_response("invalid data", 400)
    
    _rollback()
    log_error("Database data error", err, path=request.path)
    
    if request.path.startswith("/admin"):
        return render_template(
            "admin/base/errors_base.html",
            error_code=400,
            error_message="Invalid data provided."
        ), 400
    
    return render_template(
        "admin/base/errors_base.html",
        error_code=400,
        error_message="Invalid data"
    ), 400


def _handle_invalid_request(err: InvalidRequestError):
    """Handle invalid request errors."""
    # For API routes, delegate to API handlers
    if request.path.startswith("/api"):
        from quas_utils.api import error_response
        _rollback()
        log_error("Invalid request", err, path=request.path)
        return error_response("invalid request", 400)
    
    _rollback()
    log_error("Database invalid request", err, path=request.path)
    
    if request.path.startswith("/admin"):
        return render_template(
            "admin/base/errors_base.html",
            error_code=400,
            error_message="Invalid database request."
        ), 400
    
    return render_template(
        "admin/base/errors_base.html",
        error_code=400,
        error_message="Invalid request"
    ), 400


def _handle_db_operational(err: OperationalError):
    """Handle database operational errors."""
    # For API routes, delegate to API handlers
    if request.path.startswith("/api"):
        from quas_utils.api import error_response
        _rollback()
        log_error("Database operational error", err, path=request.path)
        return error_response("database error", 500)
    
    _rollback()
    log_error("Database operational error", err, path=request.path)
    
    if request.path.startswith("/admin"):
        return render_template(
            "admin/base/errors_base.html",
            error_code=503,
            error_message="Database temporarily unavailable. Please try again later."
        ), 503
    
    return render_template(
        "admin/base/errors_base.html",
        error_code=503,
        error_message="Database unavailable"
    ), 503


def _handle_db_generic(err: DatabaseError):
    """Handle generic database errors."""
    # For API routes, delegate to API handlers
    if request.path.startswith("/api"):
        from quas_utils.api import error_response
        _rollback()
        log_error("Database error", err, path=request.path)
        return error_response("database error", 500)
    
    _rollback()
    log_error("Database error", err, path=request.path)
    
    if request.path.startswith("/admin"):
        return render_template(
            "admin/base/errors_base.html",
            error_code=500,
            error_message="A database error occurred. Please try again later."
        ), 500
    
    return render_template(
        "admin/base/errors_base.html",
        error_code=500,
        error_message="Database error"
    ), 500


def add_web_db_err_handlers(bp: Blueprint):
    """
    Register database error handlers for web blueprints.
    These handlers check the path and delegate to API handlers for /api routes.
    Uses bp.register_error_handler like API handlers.
    """
    bp.register_error_handler(IntegrityError, _handle_integrity)
    bp.register_error_handler(DataError, _handle_data)
    bp.register_error_handler(InvalidRequestError, _handle_invalid_request)
    bp.register_error_handler(OperationalError, _handle_db_operational)
    bp.register_error_handler(DatabaseError, _handle_db_generic)
