"""
Admin loyalty controller.
"""

from __future__ import annotations

from flask import Response, request
import uuid

from app.extensions import db
from app.models.loyalty import LoyaltyAccount, LoyaltyLedger
from app.models.audit import AuditLog
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class AdminLoyaltyController:
    """Controller for admin loyalty endpoints."""

    @staticmethod
    def list_accounts() -> Response:
        """List all loyalty accounts."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            tier = request.args.get('tier', type=str)
            
            query = LoyaltyAccount.query
            
            if tier:
                query = query.filter_by(tier=tier)
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            accounts = [acc.to_dict() for acc in pagination.items]
            
            return success_response(
                "Loyalty accounts retrieved successfully",
                200,
                {
                    "accounts": accounts,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages
                    }
                }
            )
        except Exception as e:
            log_error("Failed to list loyalty accounts", error=e)
            return error_response("Failed to retrieve loyalty accounts", 500)

    @staticmethod
    def adjust_points(account_id: str) -> Response:
        """Manually adjust points for a loyalty account."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                account_uuid = uuid.UUID(account_id)
            except ValueError:
                return error_response("Invalid account ID format", 400)
            
            account = LoyaltyAccount.query.get(account_uuid)
            if not account:
                return error_response("Loyalty account not found", 404)
            
            from app.schemas.admin import LoyaltyAdjustRequest
            payload = LoyaltyAdjustRequest.model_validate(request.get_json() or {})
            points_delta = payload.points
            reason = payload.reason or 'Manual adjustment by admin'
            
            if points_delta is None:
                return error_response("Points delta is required", 400)
            
            old_balance = account.points_balance
            account.points_balance += points_delta
            if account.points_balance < 0:
                account.points_balance = 0
            
            # Create ledger entry
            ledger = LoyaltyLedger()
            ledger.account_id = account.id
            ledger.type = "adjust"
            ledger.points = points_delta
            ledger.reason = reason
            ledger.ref_type = "manual"
            
            db.session.add(ledger)
            db.session.commit()
            
            # Create audit log
            AuditLog.log_action(
                action="loyalty_points_adjust",
                user_id=current_user.id,
                resource_type="loyalty",
                resource_id=account_uuid,
                meta={
                    "old_balance": old_balance,
                    "new_balance": account.points_balance,
                    "points_delta": points_delta,
                    "reason": reason,
                }
            )
            
            log_event(f"Loyalty points adjusted: {account_id} by {points_delta} by admin {current_user.id}")
            
            return success_response(
                "Points adjusted successfully",
                200,
                {"account": account.to_dict()}
            )
        except Exception as e:
            log_error(f"Failed to adjust points for account {account_id}", error=e)
            db.session.rollback()
            return error_response("Failed to adjust points", 500)

