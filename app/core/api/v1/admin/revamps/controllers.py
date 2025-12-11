"""
Admin revamp controller.
"""

from __future__ import annotations

from flask import Response, request
import uuid

from app.extensions import db
from app.models.revamp import RevampRequest
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class AdminRevampController:
    """Controller for admin revamp endpoints."""

    @staticmethod
    def list_requests() -> Response:
        """List all revamp requests."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            status = request.args.get('status', type=str)
            
            query = RevampRequest.query.order_by(RevampRequest.created_at.desc())
            
            if status:
                query = query.filter_by(status=status)
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            requests = [req.to_dict() for req in pagination.items]
            
            return success_response(
                "Revamp requests retrieved successfully",
                200,
                {
                    "requests": requests,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages
                    }
                }
            )
        except Exception as e:
            log_error("Failed to list revamp requests", error=e)
            return error_response("Failed to retrieve revamp requests", 500)

    @staticmethod
    def update_request_status(request_id: str) -> Response:
        """Update revamp request status."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                request_uuid = uuid.UUID(request_id)
            except ValueError:
                return error_response("Invalid request ID format", 400)
            
            revamp_request = RevampRequest.query.get(request_uuid)
            if not revamp_request:
                return error_response("Revamp request not found", 404)
            
            from app.schemas.admin import RevampStatusUpdateRequest
            payload = RevampStatusUpdateRequest.model_validate(request.get_json() or {})
            new_status = payload.status
            assigned_to = payload.assigned_to
            
            if new_status:
                revamp_request.status = new_status
            if assigned_to:
                try:
                    staff_uuid = uuid.UUID(assigned_to)
                    revamp_request.assigned_to = staff_uuid
                except ValueError:
                    return error_response("Invalid assigned_to ID format", 400)
            
            db.session.commit()
            
            log_event(f"Revamp request status updated: {request_id} to {new_status} by admin {current_user.id}")
            
            return success_response(
                "Revamp request updated successfully",
                200,
                {"request": revamp_request.to_dict()}
            )
        except Exception as e:
            log_error(f"Failed to update revamp request {request_id}", error=e)
            db.session.rollback()
            return error_response("Failed to update revamp request", 500)

