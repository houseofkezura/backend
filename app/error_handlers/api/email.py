from __future__ import annotations

from typing import Any

from flask import Blueprint, request

from app.logging import log_error
from app.utils.helpers.api_response import error_response

try:
    from email_validator import EmailNotValidError
except Exception:  # pragma: no cover
    EmailNotValidError = type("EmailNotValidError", (), {})  # type: ignore

# Email validation errors → 400 with message
def _handle_email_invalid(err: EmailNotValidError):  # type: ignore[name-defined]
    log_error("Invalid email", err, path=request.path)
    return error_response(str(err), 400)

def add_email_err_handler(bp: Blueprint):
    bp.register_error_handler(EmailNotValidError, _handle_email_invalid)  # type: ignore[arg-type]