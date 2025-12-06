"""
Clerk authentication error handlers.

This module provides error handlers for Clerk authentication failures,
replacing the legacy JWT error handlers for customer-facing endpoints.
"""

from __future__ import annotations

from typing import Any
from flask import Blueprint, request

from app.logging import log_error
from app.utils.helpers.api_response import error_response


class ClerkAuthError(Exception):
    """Base exception for Clerk authentication errors."""
    pass


class InvalidClerkTokenError(ClerkAuthError):
    """Raised when a Clerk token is invalid or malformed."""
    pass


class ExpiredClerkTokenError(ClerkAuthError):
    """Raised when a Clerk token has expired."""
    pass


class MissingClerkTokenError(ClerkAuthError):
    """Raised when a Clerk token is missing from the request."""
    pass


class RevokedClerkTokenError(ClerkAuthError):
    """Raised when a Clerk token has been revoked."""
    pass


def _handle_invalid_token(err: InvalidClerkTokenError | Any):
    log_error("Invalid Clerk token", err, path=request.path)
    return error_response("Invalid or malformed token", 401)


def _handle_expired_token(err: ExpiredClerkTokenError | Any):
    log_error("Expired Clerk token", err, path=request.path)
    return error_response("Token expired", 401)


def _handle_missing_token(err: MissingClerkTokenError | Any):
    log_error("Missing Clerk token", err, path=request.path)
    return error_response("Authorization required", 401)


def _handle_revoked_token(err: RevokedClerkTokenError | Any):
    log_error("Revoked Clerk token", err, path=request.path)
    return error_response("Token revoked", 401)


def _handle_clerk_auth_error(err: ClerkAuthError | Any):
    log_error("Clerk authentication error", err, path=request.path)
    return error_response("Authentication failed", 401)


def add_clerk_err_handler(bp: Blueprint):
    """
    Register Clerk authentication error handlers on a blueprint.
    
    Args:
        bp: The Flask blueprint to register handlers on.
    """
    bp.register_error_handler(InvalidClerkTokenError, _handle_invalid_token)
    bp.register_error_handler(ExpiredClerkTokenError, _handle_expired_token)
    bp.register_error_handler(MissingClerkTokenError, _handle_missing_token)
    bp.register_error_handler(RevokedClerkTokenError, _handle_revoked_token)
    bp.register_error_handler(ClerkAuthError, _handle_clerk_auth_error)

