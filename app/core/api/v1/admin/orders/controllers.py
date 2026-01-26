"""
Admin order controller.
"""

from __future__ import annotations

from flask import Response, request
import uuid

from app.extensions import db
from app.models.order import Order, OrderItem
from app.models.audit import AuditLog
from app.enums.orders import OrderStatus
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class AdminOrderController:
    """Controller for admin order endpoints."""

    @staticmethod
    def list_orders() -> Response:
        """
        List all orders with optional filtering and pagination.
        
        Requires admin authentication.
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            # Get query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            status = request.args.get('status', type=str)
            user_id = request.args.get('user_id', type=str)
            search = request.args.get('search', type=str)
            
            # Build query
            query = Order.query
            
            if status:
                # Validate status is a valid OrderStatus value
                valid_statuses = [str(s) for s in OrderStatus]
                if status not in valid_statuses:
                    return error_response("Invalid status", 400)
                query = query.filter_by(status=status)
            
            if user_id:
                try:
                    user_uuid = uuid.UUID(user_id)
                    query = query.filter_by(user_id=user_uuid)
                except ValueError:
                    return error_response("Invalid user ID format", 400)
            
            if search:
                # Search by order ID or payment reference
                try:
                    order_uuid = uuid.UUID(search)
                    query = query.filter(Order.id == order_uuid)
                except ValueError:
                    query = query.filter(Order.payment_ref.ilike(f'%{search}%'))
            
            # Order by created_at desc
            query = query.order_by(Order.created_at.desc())
            
            # Paginate
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            orders = [o.to_dict(include_items=True) for o in pagination.items]
            
            return success_response(
                "Orders retrieved successfully",
                200,
                {
                    "orders": orders,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages
                    }
                }
            )
        except Exception as e:
            log_error("Failed to list orders", error=e)
            return error_response("Failed to retrieve orders", 500)

    @staticmethod
    def get_order(order_id: str) -> Response:
        """
        Get a single order by ID.
        
        Args:
            order_id: Order ID
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                order_uuid = uuid.UUID(order_id)
            except ValueError:
                return error_response("Invalid order ID format", 400)
            
            order = Order.query.get(order_uuid)
            if not order:
                return error_response("Order not found", 404)
            
            return success_response(
                "Order retrieved successfully",
                200,
                {"order": order.to_dict(include_items=True)}
            )
        except Exception as e:
            log_error(f"Failed to get order {order_id}", error=e)
            return error_response("Failed to retrieve order", 500)

    @staticmethod
    def update_order_status(order_id: str) -> Response:
        """
        Update order status (fulfill, cancel, refund, etc.).
        
        Args:
            order_id: Order ID
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                order_uuid = uuid.UUID(order_id)
            except ValueError:
                return error_response("Invalid order ID format", 400)
            
            order = Order.query.get(order_uuid)
            if not order:
                return error_response("Order not found", 404)
            
            from app.schemas.admin import OrderStatusUpdateRequest
            payload = OrderStatusUpdateRequest.model_validate(request.get_json() or {})
            new_status = payload.status
            notes = payload.notes
            
            if not new_status:
                return error_response("Status is required", 400)
            
            # Validate status is a valid OrderStatus value
            valid_statuses = [str(s) for s in OrderStatus]
            if new_status not in valid_statuses:
                return error_response("Invalid status", 400)
            
            old_status = order.status
            order.status = new_status
            db.session.commit()
            
            # Create audit log
            AuditLog.log_action(
                action="order_status_update",
                user_id=current_user.id,
                resource_type="order",
                resource_id=order_uuid,
                meta={
                    "old_status": str(old_status),
                    "new_status": new_status,
                    "notes": notes,
                }
            )
            
            log_event(f"Order status updated: {order_id} from {old_status} to {new_status} by admin {current_user.id}")
            
            # Send notification email for status change
            try:
                from app.utils.emailing import email_service
                recipient_email = order.app_user.email if order.app_user else order.guest_email
                if recipient_email:
                    # Email service method will be implemented or can use generic send
                    try:
                        if hasattr(email_service, 'send_order_status_update'):
                            email_service.send_order_status_update(
                                to=recipient_email,
                                order_id=str(order.id),
                                old_status=str(old_status.value) if hasattr(old_status, 'value') else str(old_status),
                                new_status=new_status,
                            )
                        else:
                            # Fallback: log that notification hook is ready
                            log_event(f"Order status update notification hook ready for order {order.id}")
                    except AttributeError:
                        log_event(f"Order status update notification hook ready for order {order.id}")
            except Exception as email_error:
                from app.logging import log_error
                log_error("Failed to send order status update email", error=email_error)
                # Don't fail the request if email fails
            
            return success_response(
                "Order status updated successfully",
                200,
                {"order": order.to_dict(include_items=True)}
            )
        except Exception as e:
            log_error(f"Failed to update order status {order_id}", error=e)
            db.session.rollback()
            return error_response("Failed to update order status", 500)

    @staticmethod
    def cancel_order(order_id: str) -> Response:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                order_uuid = uuid.UUID(order_id)
            except ValueError:
                return error_response("Invalid order ID format", 400)
            
            order = Order.query.get(order_uuid)
            if not order:
                return error_response("Order not found", 404)
            
            # Check if order can be cancelled
            if order.status in [str(OrderStatus.DELIVERED), str(OrderStatus.CANCELLED), str(OrderStatus.REFUNDED)]:
                return error_response(f"Cannot cancel order with status: {order.status}", 400)
            
            old_status = order.status
            order.status = str(OrderStatus.CANCELLED)
            db.session.commit()
            
            # Create audit log
            AuditLog.log_action(
                action="order_cancelled",
                user_id=current_user.id,
                resource_type="order",
                resource_id=order_uuid,
                meta={
                    "old_status": str(old_status),
                }
            )
            
            log_event(f"Order cancelled: {order_id} by admin {current_user.id}")
            
            return success_response(
                "Order cancelled successfully",
                200,
                {"order": order.to_dict(include_items=True)}
            )
        except Exception as e:
            log_error(f"Failed to cancel order {order_id}", error=e)
            db.session.rollback()
            return error_response("Failed to cancel order", 500)

