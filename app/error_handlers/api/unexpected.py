from __future__ import annotations

from typing import Any

from flask import Blueprint, request

from app.logging import log_error
from quas_utils.api import error_response
from .db import _rollback

# Catch-all → 500
def _handle_unexpected(err: Exception):
    # Only handle API routes - let web handlers deal with non-API routes
    if not request.path.startswith("/api"):
        raise err
    
    _rollback()
    log_error("Unhandled exception", err, path=request.path)
    return error_response("internal server error", 500)

def add_unexpected_err_handler(bp: Blueprint):
    bp.register_error_handler(Exception, _handle_unexpected)
