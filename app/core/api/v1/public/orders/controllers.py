from __future__ import annotations

from flask import Response, request
from flask_jwt_extended import get_jwt_identity
import uuid

from app.extensions import db
from app.utils.helpers.api_response import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.models.order import Order
from app.models.user import AppUser
from app.schemas.orders import CreateOrderRequest, UpdateOrderStatusRequest
from app.enums.orders import OrderStatus
from app.utils.esim.aggregator import EsimAggregatorClient
from app.logging import log_error


class OrdersController:
    """Controller for order management endpoints."""

    @staticmethod
    def create_order() -> Response:
        """
        Create a new pending order.
        
        If amount is not provided, fetches it from the offer.
        """
        try:
            payload = CreateOrderRequest.model_validate(request.get_json())
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            # Fetch offer to get amount if not provided
            amount = payload.amount
            if amount is None:
                client = EsimAggregatorClient()
                offer = client.get_offer_by_id(payload.offer_id)
                if not offer:
                    return error_response(f"Offer '{payload.offer_id}' not found", 404)
                amount = offer['price']
            
            # Create order
            new_order = Order()
            new_order.user_id = current_user.id
            new_order.status = OrderStatus.PENDING
            new_order.amount = amount
            
            db.session.add(new_order)
            db.session.commit()
            
            return success_response(
                "Order created successfully",
                201,
                {"order": new_order.to_dict()}
            )
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            log_error("Failed to create order", error=e)
            db.session.rollback()
            return error_response("Failed to create order", 500)

    @staticmethod
    def list_orders() -> Response:
        """List all orders for the authenticated user."""
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 8, type=int)
            
            query = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc())
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            orders: list[Order] = pagination.items
            response_data = {
                "total": pagination.total,
                "orders": [order.to_dict() for order in orders],
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
        
        Args:
            order_id: Order identifier
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                order_uuid = uuid.UUID(order_id)
            except ValueError:
                return error_response("Invalid order ID format", 400)
            
            order = Order.query.filter_by(id=order_uuid, user_id=current_user.id).first()
            
            if not order:
                return error_response(f"Order '{order_id}' not found", 404)
            
            return success_response("Order retrieved successfully", 200, {"order": order.to_dict(esim_purchases=True)})
        except Exception as e:
            log_error(f"Failed to fetch order {order_id}", error=e)
            return error_response("Failed to fetch order", 500)

    @staticmethod
    def update_order_status(order_id: str) -> Response:
        """
        Update order status.
        
        Args:
            order_id: Order identifier
        """
        try:
            payload = UpdateOrderStatusRequest.model_validate(request.get_json())
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                order_uuid = uuid.UUID(order_id)
            except ValueError:
                return error_response("Invalid order ID format", 400)
            
            order = Order.query.filter_by(id=order_uuid, user_id=current_user.id).first()
            
            if not order:
                return error_response(f"Order '{order_id}' not found", 404)
            
            # Validate status
            try:
                new_status = OrderStatus(payload.status)
            except ValueError:
                return error_response(f"Invalid status: {payload.status}", 400)
            
            order.status = new_status
            db.session.commit()
            
            return success_response("Order status updated successfully", 200, {"order": order.to_dict()})
        except ValueError as e:
            return error_response(str(e), 400)
        except Exception as e:
            log_error(f"Failed to update order {order_id}", error=e)
            db.session.rollback()
            return error_response("Failed to update order", 500)


