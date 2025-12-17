"""
CRM controller for public CRM endpoints.
"""

from __future__ import annotations

from flask import Response, request
import uuid

from app.extensions import db
from app.models.crm import CrmRating, CrmStaff
from app.models.order import Order
from app.schemas.crm import CreateRatingRequest
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.enums.orders import OrderStatus
from app.logging import log_error, log_event


class CrmController:
    """Controller for public CRM endpoints."""

    @staticmethod
    def create_rating() -> Response:
        """
        Create a rating for CRM staff who packed an order.
        
        Validates that:
        - Order is delivered
        - One rating per order (enforced by unique constraint)
        - Order belongs to the user
        """
        try:
            payload = CreateRatingRequest.model_validate(request.get_json())
            current_user = get_current_user()
            guest_email = request.args.get("email")
            
            if not current_user and not guest_email:
                return error_response("Unauthorized or email required for guest orders", 401)
            
            try:
                order_uuid = uuid.UUID(payload.order_id)
            except ValueError:
                return error_response("Invalid order ID format", 400)
            
            # Find order
            query = Order.query.filter_by(id=order_uuid)
            if current_user:
                query = query.filter_by(user_id=current_user.id)
            elif guest_email:
                query = query.filter_by(guest_email=guest_email)
            
            order = query.first()
            if not order:
                return error_response("Order not found", 404)
            
            # Validate order is delivered
            if order.status != OrderStatus.DELIVERED:
                return error_response("Can only rate orders that have been delivered", 400)
            
            # Check if rating already exists
            existing_rating = CrmRating.query.filter_by(order_id=order_uuid).first()
            if existing_rating:
                return error_response("Order has already been rated", 409)
            
            # Validate CRM staff exists
            if not order.packed_by_crm_id:
                return error_response("Order does not have an assigned CRM staff member", 400)
            
            crm_staff = CrmStaff.query.get(order.packed_by_crm_id)
            if not crm_staff:
                return error_response("CRM staff not found", 404)
            
            # Create rating
            rating = CrmRating()
            rating.order_id = order_uuid
            rating.crm_staff_id = order.packed_by_crm_id
            rating.user_id = current_user.id if current_user else None
            rating.stars = payload.stars
            rating.comment = payload.comment
            
            db.session.add(rating)
            db.session.commit()
            
            log_event(f"CRM rating created: Order {order_uuid}, Staff {order.packed_by_crm_id}, Stars {payload.stars}")
            
            return success_response(
                "Rating submitted successfully",
                201,
                {"rating": rating.to_dict()}
            )
        except Exception as e:
            log_error("Failed to create CRM rating", error=e)
            db.session.rollback()
            return error_response("Failed to submit rating", 500)






