"""Legacy placeholder; use `app.utils.emailing.service` instead."""

from __future__ import annotations

from .service import email_service as _email_service


def send_email_verification(to: str, code: str | int) -> None:
    """Backward-compatible wrapper to send verification code emails."""
    _email_service.send_verification_code(to, code)