from __future__ import annotations

from typing import Any

from flask import Blueprint, request
from werkzeug.exceptions import HTTPException, UnsupportedMediaType, NotFound, MethodNotAllowed, Unauthorized

from app.logging import log_error
from quas_utils.api import error_response

# HTTPException → use provided code/description
def _handle_http_exception(err: HTTPException):
    # Only handle API routes - let web handlers deal with non-API routes
    if not request.path.startswith("/api"):
        raise err
    
    log_error("HTTP exception", err, path=request.path)
    status = err.code or 500
    description = err.description or err.name
    return error_response(description, status)

# 415 Unsupported Media Type
def _handle_unsupported_media_type(err: UnsupportedMediaType):
    # Only handle API routes - let web handlers deal with non-API routes
    if not request.path.startswith("/api"):
        raise err
    
    log_error("Unsupported media type", err, path=request.path)
    return error_response("unsupported media type", 415)

def _handle_not_found(err: NotFound):
    # Only handle API routes - let web handlers deal with non-API routes
    if not request.path.startswith("/api"):
        raise err
    
    log_error("Not found", err, path=request.path)
    return error_response("Resource not found", 404)

def _handle_method_not_allowed(err: MethodNotAllowed):
    # Only handle API routes - let web handlers deal with non-API routes
    if not request.path.startswith("/api"):
        raise err
    
    log_error("Method not allowed", err, path=request.path)
    return error_response("Method not allowed", 405)

def _handle_unauthorized(err: Unauthorized):
    # Only handle API routes - let web handlers deal with non-API routes
    if not request.path.startswith("/api"):
        raise err
    
    log_error("Unauthorized", err, path=request.path)
    return error_response("Unauthorized", 401)

def add_http_err_handlers(bp: Blueprint):
    bp.app_errorhandler(HTTPException)(_handle_http_exception)

    # 415 Unsupported Media Type
    bp.app_errorhandler(UnsupportedMediaType)(_handle_unsupported_media_type)
    
    bp.app_errorhandler(NotFound)(_handle_not_found)
    bp.app_errorhandler(MethodNotAllowed)(_handle_method_not_allowed)
    bp.app_errorhandler(Unauthorized)(_handle_unauthorized)
