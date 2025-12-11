from __future__ import annotations

from typing import Any

from flask import Blueprint, request
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InvalidRequestError,
    OperationalError,
)

from app.logging import log_error
from quas_utils.api import error_response

# Database errors → rollback and return appropriate code
def _rollback():
    try:
        from app.extensions import db  # lazy import to avoid circulars
        db.session.rollback()
    except Exception:
        pass

def _handle_integrity(err: IntegrityError):
        _rollback()
        log_error("Integrity error", err, path=request.path)
        return error_response("conflict with existing data", 409)

def _handle_data(err: DataError):
        _rollback()
        log_error("Invalid data", err, path=request.path)
        return error_response("invalid data", 400)

def _handle_invalid_request(err: InvalidRequestError):
        _rollback()
        log_error("Invalid request", err, path=request.path)
        return error_response("invalid request", 400)

def _handle_db_operational(err: OperationalError):
        _rollback()
        log_error("Database operational error", err, path=request.path)
        return error_response("database error", 500)

def _handle_db_generic(err: DatabaseError):
        _rollback()
        log_error("Database error", err, path=request.path)
        return error_response("database error", 500)


def add_db_err_handlers(bp: Blueprint):
    bp.register_error_handler(IntegrityError, _handle_integrity)
    bp.register_error_handler(DataError, _handle_data)
    bp.register_error_handler(InvalidRequestError, _handle_invalid_request)
    bp.register_error_handler(OperationalError, _handle_db_operational)
    bp.register_error_handler(DatabaseError, _handle_db_generic)