from __future__ import annotations

from flask import Response
from sqlalchemy import func

from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.models.order import Order
from app.models.payment import Payment
from app.enums.orders import OrderStatus
from app.enums.payments import PaymentStatus
from app.logging import log_error


class StatsController:
    """Controller for system-wide statistics endpoints."""

    @staticmethod
    def get_stats() -> Response:
        """
        Get comprehensive statistics for the authenticated user.
        
        Returns:
            Statistics including eSIM purchases, orders, payments, and totals
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            
            # Order Statistics
            order_base_query = Order.query.filter_by(user_id=current_user.id)
            
            order_stats = {
                "total_orders": order_base_query.count(),
                "pending_orders": order_base_query.filter(
                    Order.status.in_([str(OrderStatus.PENDING), str(OrderStatus.AWAITING_PAYMENT)])
                ).count(),
                "paid_orders": order_base_query.filter(Order.status == str(OrderStatus.PAID)).count(),
                "processing_orders": order_base_query.filter(Order.status == str(OrderStatus.PROCESSING)).count(),
                "completed_orders": order_base_query.filter(
                    Order.status.in_([str(OrderStatus.DELIVERED), str(OrderStatus.SHIPPED)])
                ).count(),
                "cancelled_orders": order_base_query.filter(
                    Order.status.in_([str(OrderStatus.CANCELLED), str(OrderStatus.FAILED)])
                ).count(),
            }
            
            # Calculate order total spent
            paid_orders = order_base_query.filter(Order.status == str(OrderStatus.PAID)).all()
            order_total_spent = sum(float(o.amount) for o in paid_orders)
            order_stats["total_spent"] = round(order_total_spent, 2)
            
            # Payment Statistics
            payment_base_query = Payment.query.filter_by(user_id=current_user.id)
            
            payment_stats = {
                "total_payments": payment_base_query.count(),
                "pending_payments": payment_base_query.filter_by(status=str(PaymentStatus.PENDING)).count(),
                "processing_payments": payment_base_query.filter_by(status=str(PaymentStatus.PROCESSING)).count(),
                "completed_payments": payment_base_query.filter_by(status=str(PaymentStatus.COMPLETED)).count(),
                "failed_payments": payment_base_query.filter(
                    Payment.status.in_([str(PaymentStatus.FAILED), str(PaymentStatus.CANCELLED), str(PaymentStatus.EXPIRED)])
                ).count(),
            }
            
            # Calculate payment totals
            completed_payments = payment_base_query.filter_by(status=str(PaymentStatus.COMPLETED)).all()
            payment_total_amount = sum(float(p.amount) for p in completed_payments)
            payment_stats["total_amount"] = round(payment_total_amount, 2)
            
            # Overall Statistics
            overall_stats = {
                "total_spent_ngn": round( order_total_spent, 2),
            }
            
            stats = {
                "orders": order_stats,
                "payments": payment_stats,
                "overall": overall_stats,
            }
            
            return success_response("Statistics retrieved successfully", 200, stats)
        except Exception as e:
            log_error("Failed to fetch statistics", error=e)
            return error_response("Failed to fetch statistics", 500)

