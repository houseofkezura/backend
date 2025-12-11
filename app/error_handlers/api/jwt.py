from __future__ import annotations

from typing import Any

from flask import Blueprint, request
from werkzeug.exceptions import HTTPException, UnsupportedMediaType

from app.logging import log_error
from quas_utils.api import error_response

try:  # jwt-related exceptions are optional at import time
    from flask_jwt_extended.exceptions import (
        JWTDecodeError,
        NoAuthorizationError,
        InvalidHeaderError,
        WrongTokenError,
        RevokedTokenError,
        FreshTokenRequired,
        CSRFError,
    )
except Exception:  # pragma: no cover - package presence varies
    JWTDecodeError = type("JWTDecodeError", (), {})  # type: ignore
    NoAuthorizationError = type("NoAuthorizationError", (), {})  # type: ignore
    InvalidHeaderError = type("InvalidHeaderError", (), {})  # type: ignore
    WrongTokenError = type("WrongTokenError", (), {})  # type: ignore
    RevokedTokenError = type("RevokedTokenError", (), {})  # type: ignore
    FreshTokenRequired = type("FreshTokenRequired", (), {})  # type: ignore
    CSRFError = type("CSRFError", (), {})  # type: ignore

try:
    from jwt import ExpiredSignatureError
except Exception:  # pragma: no cover
    ExpiredSignatureError = type("ExpiredSignatureError", (), {})  # type: ignore


# JWT / auth errors → 401/403
def _handle_jwt_decode(err: JWTDecodeError):  # type: ignore[name-defined]
    log_error("Invalid token", err, path=request.path)
    return error_response("invalid token", 401)

def _handle_expired(err: ExpiredSignatureError):  # type: ignore[name-defined]
    log_error("Token expired", err, path=request.path)
    return error_response("token expired", 401)

def _handle_no_auth(err: NoAuthorizationError):  # type: ignore[name-defined]
    log_error("Authorization missing", err, path=request.path)
    return error_response("authorization required", 401)

def _handle_invalid_header(err: InvalidHeaderError):  # type: ignore[name-defined]
    log_error("Invalid auth header", err, path=request.path)
    return error_response("invalid authorization header", 401)

def _handle_wrong_token(err: WrongTokenError):  # type: ignore[name-defined]
    log_error("Wrong token", err, path=request.path)
    return error_response("wrong token type", 401)

def _handle_revoked(err: RevokedTokenError):  # type: ignore[name-defined]
    log_error("Revoked token", err, path=request.path)
    return error_response("token revoked", 401)

def _handle_fresh_required(err: FreshTokenRequired):  # type: ignore[name-defined]
    log_error("Fresh token required", err, path=request.path)
    return error_response("fresh token required", 401)

def _handle_csrf(err: CSRFError):  # type: ignore[name-defined]
    log_error("CSRF error", err, path=request.path)
    return error_response("csrf error", 401)

def add_jwt_err_handler(bp: Blueprint):
    bp.register_error_handler(JWTDecodeError, _handle_jwt_decode)  # type: ignore[arg-type]
    bp.register_error_handler(ExpiredSignatureError, _handle_expired)  # type: ignore[arg-type]
    bp.register_error_handler(NoAuthorizationError, _handle_no_auth)  # type: ignore[arg-type]
    bp.register_error_handler(InvalidHeaderError, _handle_invalid_header)  # type: ignore[arg-type]
    bp.register_error_handler(WrongTokenError, _handle_wrong_token)  # type: ignore[arg-type]
    bp.register_error_handler(RevokedTokenError, _handle_revoked)  # type: ignore[arg-type]
    bp.register_error_handler(FreshTokenRequired, _handle_fresh_required)  # type: ignore[arg-type]
    bp.register_error_handler(CSRFError, _handle_csrf)  # type: ignore[arg-type]