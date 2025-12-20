"""
Admin CRM controller.
"""

from __future__ import annotations

from flask import Response, request
import uuid

from app.extensions import db
from app.models.crm import CrmRating
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class AdminCrmController:
    """Controller for admin CRM endpoints."""

    @staticmethod
    def list_ratings() -> Response:
        """List all CRM ratings."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            staff_id = request.args.get('staff_id', type=str)
            
            query = CrmRating.query.order_by(CrmRating.created_at.desc())
            
            if staff_id:
                try:
                    staff_uuid = uuid.UUID(staff_id)
                    query = query.filter_by(crm_staff_id=staff_uuid)
                except ValueError:
                    return error_response("Invalid staff ID format", 400)
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            ratings = [r.to_dict() for r in pagination.items]
            
            return success_response(
                "CRM ratings retrieved successfully",
                200,
                {
                    "ratings": ratings,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages
                    }
                }
            )
        except Exception as e:
            log_error("Failed to list CRM ratings", error=e)
            return error_response("Failed to retrieve CRM ratings", 500)







