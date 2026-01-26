"""
Waitlist controller for public endpoints.
"""

from __future__ import annotations

from flask import Response, request
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.waitlist import WaitlistEntry
from app.schemas.waitlist import CreateWaitlistEntryRequest
from app.enums.waitlist import WaitlistStatus
from quas_utils.api import success_response, error_response
from app.logging import log_error, log_event


class WaitlistController:
    """Controller for public waitlist endpoints."""

    @staticmethod
    def join_waitlist() -> Response:
        """
        Join the waitlist.
        
        Public endpoint - no authentication required.
        """
        try:
            payload = CreateWaitlistEntryRequest.model_validate(request.get_json())
            
            # Check if email already exists
            existing_entry = WaitlistEntry.query.filter_by(email=payload.email.lower()).first()
            if existing_entry:
                return error_response(
                    "This email is already on the waitlist",
                    409
                )
            
            # Create waitlist entry
            entry = WaitlistEntry()
            entry.email = payload.email.lower()
            entry.status = str(WaitlistStatus.PENDING)
            
            db.session.add(entry)
            db.session.commit()
            
            log_event(f"Waitlist entry created: {entry.id} for {payload.email}")
            
            return success_response(
                "Successfully joined the waitlist! We'll notify you when we launch.",
                201,
                {"entry_id": str(entry.id)}
            )
        except IntegrityError:
            db.session.rollback()
            return error_response("This email is already on the waitlist", 409)
        except Exception as e:
            log_error("Failed to create waitlist entry", error=e)
            db.session.rollback()
            return error_response("Failed to join waitlist", 500)

    @staticmethod
    def check_status() -> Response:
        """
        Check if an email is on the waitlist and get its status.
        
        Public endpoint - no authentication required.
        """
        try:
            email = request.args.get('email', '').lower().strip()
            if not email:
                return error_response("Email parameter is required", 400)
            
            entry = WaitlistEntry.query.filter_by(email=email).first()
            
            if entry:
                return success_response(
                    "Email found on waitlist",
                    200,
                    {
                        "email": entry.email,
                        "is_on_waitlist": True,
                        "status": entry.status,
                        "entry_id": str(entry.id)
                    }
                )
            else:
                return success_response(
                    "Email not found on waitlist",
                    200,
                    {
                        "email": email,
                        "is_on_waitlist": False,
                        "status": None,
                        "entry_id": None
                    }
                )
        except Exception as e:
            log_error("Failed to check waitlist status", error=e)
            return error_response("Failed to check waitlist status", 500)
