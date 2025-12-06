"""Emailing utilities and service exports."""

from .service import EmailService, email_service  # re-export

__all__ = ["EmailService", "email_service"]