from __future__ import annotations

from flask import Response, request
import uuid

from app.extensions import db
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.models.order import Order
from app.models.user import AppUser
from app.enums.orders import OrderStatus
from app.logging import log_error


class OrdersController:
    """Controller for order management endpoints."""

    @staticmethod
    def cancel_order(order_id: str) -> Response:
        """
        Cancel an order.
        
        Only orders that haven't been shipped can be cancelled.
        """
        try:
            current_user = get_current_user()
            guest_email = request.args.get("email")  # For guest orders
            
            if not current_user and not guest_email:
                return error_response("Unauthorized", 401)
            
            try:
                order_uuid = uuid.UUID(order_id)
            except ValueError:
                return error_response("Invalid order ID format", 400)
            
            # Find order
            query = Order.query.filter_by(id=order_uuid)
            if current_user:
                query = query.filter_by(user_id=current_user.id)
            elif guest_email:
                query = query.filter_by(guest_email=guest_email)
            else:
                return error_response("Unauthorized", 401)
            
            order = query.first()
            if not order:
                return error_response("Order not found", 404)
            
            # Check if order can be cancelled
            if order.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
                return error_response("Cannot cancel order that has been shipped", 400)
            
            order.status = OrderStatus.CANCELLED
            db.session.commit()
            
            return success_response(
                "Order cancelled successfully",
                200,
                {"order": order.to_dict(include_items=True)}
            )
        except Exception as e:
            log_error(f"Failed to cancel order {order_id}", error=e)
            db.session.rollback()
            return error_response("Failed to cancel order", 500)

    @staticmethod
    def list_orders() -> Response:
        """
        List all orders for the authenticated user or guest.
        
        For guests, requires email query parameter.
        """
        try:
            current_user = get_current_user()
            guest_email = request.args.get("email")
            
            if not current_user and not guest_email:
                return error_response("Unauthorized or email required for guest orders", 401)
            
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 20, type=int)
            
            query = Order.query
            if current_user:
                query = query.filter_by(user_id=current_user.id)
            elif guest_email:
                query = query.filter_by(guest_email=guest_email)
            
            query = query.order_by(Order.created_at.desc())
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            orders: list[Order] = pagination.items
            response_data = {
                "total": pagination.total,
                "orders": [order.to_dict(include_items=True) for order in orders],
                "current_page": pagination.page,
                "total_pages": pagination.pages,
            }
            
            return success_response(
                "Orders retrieved successfully",
                200,
                response_data
            )
        except Exception as e:
            log_error("Failed to fetch orders", error=e)
            return error_response("Failed to fetch orders", 500)

    @staticmethod
    def get_order(order_id: str) -> Response:
        """
        Get a specific order by ID.
        
        Supports both authenticated users and guest orders (via email query param).
        
        Args:
            order_id: Order identifier
        """
        try:
            current_user = get_current_user()
            guest_email = request.args.get("email")
            
            if not current_user and not guest_email:
                return error_response("Unauthorized or email required for guest orders", 401)
            
            try:
                order_uuid = uuid.UUID(order_id)
            except ValueError:
                return error_response("Invalid order ID format", 400)
            
            query = Order.query.filter_by(id=order_uuid)
            if current_user:
                query = query.filter_by(user_id=current_user.id)
            elif guest_email:
                query = query.filter_by(guest_email=guest_email)
            
            order = query.first()
            
            if not order:
                return error_response(f"Order '{order_id}' not found", 404)
            
            return success_response(
                "Order retrieved successfully",
                200,
                {"order": order.to_dict(include_items=True)}
            )
        except Exception as e:
            log_error(f"Failed to fetch order {order_id}", error=e)
            return error_response("Failed to fetch order", 500)



