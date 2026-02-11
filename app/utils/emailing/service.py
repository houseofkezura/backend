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

    def send_order_confirmation(
        self,
        to: str,
        order: Any,
        items: list[dict[str, Any]] | None = None,
        *,
        context: Mapping[str, Any] | None = None,
        subject_prefix: str = "Order Confirmation"
    ) -> None:
        """
        Send order confirmation email with order details and tracking link.
        
        Args:
            to: Recipient email address
            order: Order model instance
            items: List of order item dicts with 'variant', 'quantity', 'unit_price'
            context: Additional context for template
            subject_prefix: Email subject prefix (default: "Order Confirmation")
        """
        from datetime import datetime
        from ..helpers.site import get_platform_url
        
        # Build tracking URL
        platform_url = get_platform_url()
        tracking_url = f"{platform_url}/orders/{order.order_number}"
        
        # Extract customer name from shipping address or order
        shipping_address = order.shipping_address or {}
        customer_name = shipping_address.get("name") or shipping_address.get("first_name", "")
        
        # Format items for template
        formatted_items = []
        if items:
            for item in items:
                variant = item.get("variant")
                formatted_items.append({
                    "name": variant.sku if variant else "Unknown Item",
                    "quantity": item.get("quantity", 1),
                    "unit_price": float(item.get("unit_price", 0)),
                    "variant": {"sku": variant.sku if variant else ""},
                })
        elif hasattr(order, "items") and order.items:
            for order_item in order.items:
                formatted_items.append({
                    "name": order_item.variant.sku if order_item.variant else "Unknown Item",
                    "quantity": order_item.quantity,
                    "unit_price": float(order_item.unit_price),
                    "variant": {"sku": order_item.variant.sku if order_item.variant else ""},
                })
        
        merged_context = {
            "order_number": order.order_number,
            "customer_name": customer_name,
            "items": formatted_items,
            "subtotal": float(order.subtotal),
            "shipping_cost": float(order.shipping_cost),
            "discount": float(order.discount),
            "total": float(order.total),
            "currency": order.currency or "NGN",
            "shipping_address": shipping_address,
            "tracking_url": tracking_url,
            "current_year": datetime.now().year,
            **(context or {})
        }
        self.send_html(
            to,
            f"{subject_prefix} - {order.order_number}",
            "mail/order-confirmation.html",
            merged_context
        )

    
    def send_order_status_update(
        self,
        to: str,
        order: Any,
        new_status: str,
        notes: str | None = None,
        *,
        context: Mapping[str, Any] | None = None
    ) -> None:
        """
        Send email notification when order status changes.
        
        Args:
            to: Recipient email
            order: Order model instance
            new_status: New status string (e.g., 'shipped', 'delivered')
            notes: Optional notes from admin
            context: Additional context
        """
        from datetime import datetime
        from ..helpers.site import get_platform_url
        
        # Build tracking URL
        platform_url = get_platform_url()
        tracking_url = f"{platform_url}/orders/{order.order_number}"
        
        # Extract customer name
        shipping_address = order.shipping_address or {}
        customer_name = shipping_address.get("name") or shipping_address.get("first_name", "")
        
        merged_context = {
            "order_number": order.order_number,
            "customer_name": customer_name,
            "new_status": new_status,
            "notes": notes,
            "tracking_url": tracking_url,
            "current_year": datetime.now().year,
            **(context or {})
        }
        
        self.send_html(
            to,
            f"Order Update - {order.order_number}",
            "mail/order-status-update.html",
            merged_context
        )

    def send_payment_received(
        self,
        to: str,
        order: Any,
        *,
        context: Mapping[str, Any] | None = None
    ) -> None:
        """
        Send payment received confirmation.
        
        Reuses order confirmation template with updated title.
        """
        self.send_order_confirmation(
            to, 
            order, 
            context={"title": "Payment Received", **(context or {})},
            subject_prefix="Payment Received"
        )

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


