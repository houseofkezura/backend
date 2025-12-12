"""
Revamp request controller for public endpoints.
"""

from __future__ import annotations

from flask import Response, request
import uuid

from app.extensions import db
from app.models.revamp import RevampRequest
from app.models.order import OrderItem
from app.schemas.revamp import CreateRevampRequest
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class RevampController:
    """Controller for public revamp request endpoints."""

    @staticmethod
    def create_revamp_request() -> Response:
        """
        Create a new revamp request.
        
        Requires authentication.
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            payload = CreateRevampRequest.model_validate(request.get_json())
            
            try:
                order_item_uuid = uuid.UUID(payload.order_item_id)
            except ValueError:
                return error_response("Invalid order item ID format", 400)
            
            # Verify order item belongs to user
            order_item = OrderItem.query.get(order_item_uuid)
            if not order_item:
                return error_response("Order item not found", 404)
            
            if order_item.order.user_id != current_user.id:
                return error_response("Order item does not belong to you", 403)
            
            # Create revamp request
            revamp_request = RevampRequest()
            revamp_request.user_id = current_user.id
            revamp_request.order_item_id = order_item_uuid
            revamp_request.description = payload.description
            revamp_request.images = payload.images or []
            revamp_request.status = "pending"
            
            db.session.add(revamp_request)
            db.session.commit()
            
            log_event(f"Revamp request created: {revamp_request.id} for order item {order_item_uuid}")
            
            return success_response(
                "Revamp request created successfully",
                201,
                {"revamp_request": revamp_request.to_dict()}
            )
        except Exception as e:
            log_error("Failed to create revamp request", error=e)
            db.session.rollback()
            return error_response("Failed to create revamp request", 500)

    @staticmethod
    def get_revamp_status(revamp_id: str) -> Response:
        """
        Get revamp request status.
        
        Args:
            revamp_id: Revamp request ID
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                revamp_uuid = uuid.UUID(revamp_id)
            except ValueError:
                return error_response("Invalid revamp ID format", 400)
            
            revamp_request = RevampRequest.query.filter_by(
                id=revamp_uuid,
                user_id=current_user.id
            ).first()
            
            if not revamp_request:
                return error_response("Revamp request not found", 404)
            
            return success_response(
                "Revamp request retrieved successfully",
                200,
                {"revamp_request": revamp_request.to_dict()}
            )
        except Exception as e:
            log_error(f"Failed to get revamp request {revamp_id}", error=e)
            return error_response("Failed to retrieve revamp request", 500)





