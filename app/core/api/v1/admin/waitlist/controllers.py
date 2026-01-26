"""
Admin waitlist controller.
"""

from __future__ import annotations

from flask import Response, request
import uuid
from datetime import datetime

from app.extensions import db
from app.models.waitlist import WaitlistEntry
from app.enums.waitlist import WaitlistStatus
from app.schemas.waitlist import UpdateWaitlistStatusRequest
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event
from quas_utils.date_time import QuasDateTime


class AdminWaitlistController:
    """Controller for admin waitlist endpoints."""

    @staticmethod
    def list_entries() -> Response:
        """List all waitlist entries with pagination and filters."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            status = request.args.get('status', type=str)
            search = request.args.get('search', type=str)
            
            query = WaitlistEntry.query.order_by(WaitlistEntry.created_at.desc())
            
            if status:
                query = query.filter_by(status=status)
            
            if search:
                search_term = f"%{search}%"
                query = query.filter(WaitlistEntry.email.ilike(search_term))
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            entries = [entry.to_dict() for entry in pagination.items]
            
            return success_response(
                "Waitlist entries retrieved successfully",
                200,
                {
                    "entries": entries,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages
                    }
                }
            )
        except Exception as e:
            log_error("Failed to list waitlist entries", error=e)
            return error_response("Failed to retrieve waitlist entries", 500)

    @staticmethod
    def update_status(entry_id: str) -> Response:
        """Update waitlist entry status."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                entry_uuid = uuid.UUID(entry_id)
            except ValueError:
                return error_response("Invalid entry ID format", 400)
            
            entry = WaitlistEntry.query.get(entry_uuid)
            if not entry:
                return error_response("Waitlist entry not found", 404)
            
            payload = UpdateWaitlistStatusRequest.model_validate(request.get_json() or {})
            new_status = payload.status
            
            if not new_status:
                return error_response("Status is required", 400)
            
            # Validate status value
            valid_statuses = [str(WaitlistStatus.PENDING), str(WaitlistStatus.INVITED), str(WaitlistStatus.CONVERTED)]
            if new_status not in valid_statuses:
                return error_response(f"Invalid status. Must be one of: {', '.join(valid_statuses)}", 400)
            
            old_status = entry.status
            entry.status = new_status
            
            # Update timestamps based on status
            if new_status == str(WaitlistStatus.INVITED) and not entry.invited_at:
                entry.invited_at = QuasDateTime.aware_utcnow()
            elif new_status == str(WaitlistStatus.CONVERTED) and not entry.converted_at:
                entry.converted_at = QuasDateTime.aware_utcnow()
            
            db.session.commit()
            
            log_event(f"Waitlist entry status updated: {entry_id} from {old_status} to {new_status} by admin {current_user.id}")
            
            return success_response(
                "Waitlist entry status updated successfully",
                200,
                {"entry": entry.to_dict()}
            )
        except Exception as e:
            log_error(f"Failed to update waitlist entry {entry_id}", error=e)
            db.session.rollback()
            return error_response("Failed to update waitlist entry", 500)

    @staticmethod
    def delete_entry(entry_id: str) -> Response:
        """Delete a waitlist entry."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                entry_uuid = uuid.UUID(entry_id)
            except ValueError:
                return error_response("Invalid entry ID format", 400)
            
            entry = WaitlistEntry.query.get(entry_uuid)
            if not entry:
                return error_response("Waitlist entry not found", 404)
            
            email = entry.email
            db.session.delete(entry)
            db.session.commit()
            
            log_event(f"Waitlist entry deleted: {entry_id} ({email}) by admin {current_user.id}")
            
            return success_response(
                "Waitlist entry deleted successfully",
                200,
                {"message": "Entry deleted successfully"}
            )
        except Exception as e:
            log_error(f"Failed to delete waitlist entry {entry_id}", error=e)
            db.session.rollback()
            return error_response("Failed to delete waitlist entry", 500)

    @staticmethod
    def get_stats() -> Response:
        """Get waitlist statistics."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            total = WaitlistEntry.query.count()
            pending = WaitlistEntry.query.filter_by(status=str(WaitlistStatus.PENDING)).count()
            invited = WaitlistEntry.query.filter_by(status=str(WaitlistStatus.INVITED)).count()
            converted = WaitlistEntry.query.filter_by(status=str(WaitlistStatus.CONVERTED)).count()
            
            return success_response(
                "Waitlist statistics retrieved successfully",
                200,
                {
                    "total": total,
                    "pending": pending,
                    "invited": invited,
                    "converted": converted
                }
            )
        except Exception as e:
            log_error("Failed to get waitlist statistics", error=e)
            return error_response("Failed to retrieve waitlist statistics", 500)
