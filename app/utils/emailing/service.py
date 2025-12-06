"""Email service utilities built on Flask-Mail with Jinja templates."""

from __future__ import annotations

from threading import Thread
from typing import Any, Mapping

from flask import current_app, render_template
from flask_mail import Message

from config import Config
from app.extensions import mail
from app.logging import log_error


class EmailService:
    """High-level email sending service.

    Provides helpers for rendering Jinja templates and sending messages
    asynchronously using a background thread.
    """

    def send_html(self, to: str | list[str], subject: str, template: str, context: Mapping[str, Any] | None = None, *, reply_to: str | None = None) -> None:
        """Render a Jinja template and send an HTML email asynchronously."""
        recipients: list[str] = [to] if isinstance(to, str) else list(to)
        html_body: str = render_template(template, **(context or {}))

        message = Message(
            subject=subject,
            sender=Config.MAIL_ALIAS,
            recipients=recipients,
            reply_to=reply_to or Config.MAIL_USERNAME,
            html=html_body,
        )

        self._send_async(message)

    def send_verification_code(self, to: str, code: str | int, *, expires_minutes: int = 15, context: Mapping[str, Any] | None = None) -> None:
        """Send a verification code email using default template."""
        merged_context = {"code": code, "expires_minutes": expires_minutes, **(context or {})}
        self.send_html(to, "Your Verification Code", "mail/send-code.html", merged_context)

    def send_esim_redemption_email(self, to: str, esim_purchase: Any, *, context: Mapping[str, Any] | None = None) -> None:
        """
        Send eSIM redemption email with QR code.
        
        Args:
            to: Recipient email address
            esim_purchase: EsimPurchase model instance
            context: Additional context for template
        """
        merged_context = {
            "offer_id": esim_purchase.offer_id,
            "qr_code": esim_purchase.esim_qr or "",
            "activation_code": esim_purchase.activation_code or "",
            "smdp": esim_purchase.smdp or "",
            **(context or {})
        }
        self.send_html(to, "Your eSIM is Ready!", "mail/esim-activation.html", merged_context)

    def _send_async(self, message: Message) -> None:
        """Queue email send on a background thread."""
        # Capture the current app instance before the thread
        app = current_app._get_current_object()  # type: ignore[attr-defined]
        
        def _target():
            try:
                with app.app_context():
                    mail.send(message)
            except Exception as e:
                with app.app_context():
                    log_error("Email send failed", e)

        Thread(target=_target, daemon=True).start()


# Singleton-like convenience
email_service = EmailService()


