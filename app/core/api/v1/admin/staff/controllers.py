"""
Admin CRM staff controller.
"""

from __future__ import annotations

from flask import Response, request
import uuid

from app.extensions import db
from app.models.crm import CrmStaff, CrmRating
from app.utils.helpers.api_response import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class AdminStaffController:
    """Controller for admin CRM staff endpoints."""

    @staticmethod
    def list_staff() -> Response:
        """List all CRM staff."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            
            query = CrmStaff.query.order_by(CrmStaff.created_at.desc())
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            staff_list = []
            for staff in pagination.items:
                staff_dict = staff.to_dict()
                # Add rating stats
                ratings = CrmRating.query.filter_by(crm_staff_id=staff.id).all()
                if ratings:
                    avg_rating = sum(r.stars for r in ratings) / len(ratings)
                    staff_dict['avg_rating'] = round(avg_rating, 2)
                    staff_dict['total_ratings'] = len(ratings)
                else:
                    staff_dict['avg_rating'] = None
                    staff_dict['total_ratings'] = 0
                staff_list.append(staff_dict)
            
            return success_response(
                "Staff retrieved successfully",
                200,
                {
                    "staff": staff_list,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages
                    }
                }
            )
        except Exception as e:
            log_error("Failed to list staff", error=e)
            return error_response("Failed to retrieve staff", 500)

    @staticmethod
    def create_staff() -> Response:
        """Create a new CRM staff member."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            from app.schemas.admin import StaffCreateRequest
            payload = StaffCreateRequest.model_validate(request.get_json() or {})
            
            # Check if staff_code exists
            existing = CrmStaff.query.filter_by(staff_code=payload.staff_code).first()
            if existing:
                return error_response("Staff code already exists", 409)
            
            staff = CrmStaff()
            staff.name = payload.name
            staff.staff_code = payload.staff_code
            staff.contact = payload.contact
            staff.role = payload.role
            
            db.session.add(staff)
            db.session.commit()
            
            log_event(f"CRM staff created: {staff_code} by admin {current_user.id}")
            
            return success_response(
                "Staff created successfully",
                201,
                {"staff": staff.to_dict()}
            )
        except Exception as e:
            log_error("Failed to create staff", error=e)
            db.session.rollback()
            return error_response("Failed to create staff", 500)

