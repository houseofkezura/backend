"""
Admin B2B controller.
"""

from __future__ import annotations

from flask import Response, request
import uuid

from app.extensions import db
from app.models.cms import B2BInquiry
from app.utils.helpers.api_response import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class AdminB2BController:
    """Controller for admin B2B endpoints."""

    @staticmethod
    def list_inquiries() -> Response:
        """List all B2B inquiries."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            status = request.args.get('status', type=str)
            
            query = B2BInquiry.query.order_by(B2BInquiry.created_at.desc())
            
            if status:
                query = query.filter_by(status=status)
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            inquiries = [inq.to_dict() for inq in pagination.items]
            
            return success_response(
                "B2B inquiries retrieved successfully",
                200,
                {
                    "inquiries": inquiries,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages
                    }
                }
            )
        except Exception as e:
            log_error("Failed to list B2B inquiries", error=e)
            return error_response("Failed to retrieve B2B inquiries", 500)

    @staticmethod
    def update_inquiry_status(inquiry_id: str) -> Response:
        """Update B2B inquiry status."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                inquiry_uuid = uuid.UUID(inquiry_id)
            except ValueError:
                return error_response("Invalid inquiry ID format", 400)
            
            inquiry = B2BInquiry.query.get(inquiry_uuid)
            if not inquiry:
                return error_response("B2B inquiry not found", 404)
            
            from app.schemas.admin import B2BUpdateStatusRequest
            payload = B2BUpdateStatusRequest.model_validate(request.get_json() or {})
            new_status = payload.status
            note = payload.note
            
            if new_status:
                inquiry.status = new_status
            if note:
                inquiry.note = note
            
            db.session.commit()
            
            log_event(f"B2B inquiry status updated: {inquiry_id} to {new_status} by admin {current_user.id}")
            
            return success_response(
                "Inquiry status updated successfully",
                200,
                {"inquiry": inquiry.to_dict()}
            )
        except Exception as e:
            log_error(f"Failed to update B2B inquiry {inquiry_id}", error=e)
            db.session.rollback()
            return error_response("Failed to update inquiry", 500)

