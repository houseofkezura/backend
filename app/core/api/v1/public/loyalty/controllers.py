"""
Loyalty controller for public loyalty endpoints.
"""

from __future__ import annotations

from flask import Response, request
from typing import Optional

from app.extensions import db
from app.models.loyalty import (
    LoyaltyAccount,
    LoyaltyLedger,
    LOYALTY_TIER_MUSE,
    LOYALTY_TIER_ICON,
    LOYALTY_TIER_EMPRESS,
)
from app.schemas.loyalty import RedeemPointsRequest, LoyaltyLedgerFilter
from app.utils.helpers.api_response import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class LoyaltyController:
    """Controller for public loyalty endpoints."""

    @staticmethod
    def get_loyalty_info() -> Response:
        """
        Get current user's loyalty account information.
        
        Returns tier, points balance, and progress to next tier.
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            # Get or create loyalty account
            loyalty_account = LoyaltyAccount.query.filter_by(user_id=current_user.id).first()
            
            if not loyalty_account:
                # Create default Muse tier account
                loyalty_account = LoyaltyAccount()
                loyalty_account.user_id = current_user.id
                loyalty_account.tier = LOYALTY_TIER_MUSE
                loyalty_account.points_balance = 0
                loyalty_account.lifetime_spend = 0
                db.session.add(loyalty_account)
                db.session.commit()
            
            # Calculate progress to next tier
            progress = {
                "current_tier": loyalty_account.tier,
                "points_balance": loyalty_account.points_balance,
                "lifetime_spend": float(loyalty_account.lifetime_spend),
            }
            
            # Determine next tier and threshold
            if loyalty_account.tier == LOYALTY_TIER_MUSE:
                progress["next_tier"] = LOYALTY_TIER_ICON
                progress["threshold"] = 500000  # ₦500k
                progress["progress_percentage"] = min(100, (float(loyalty_account.lifetime_spend) / 500000) * 100)
            elif loyalty_account.tier == LOYALTY_TIER_ICON:
                progress["next_tier"] = LOYALTY_TIER_EMPRESS
                progress["threshold"] = 1200000  # ₦1.2M
                progress["progress_percentage"] = min(100, (float(loyalty_account.lifetime_spend) / 1200000) * 100)
            else:
                progress["next_tier"] = None
                progress["threshold"] = None
                progress["progress_percentage"] = 100
            
            return success_response(
                "Loyalty information retrieved successfully",
                200,
                {
                    "loyalty_account": loyalty_account.to_dict(),
                    "progress": progress,
                }
            )
        except Exception as e:
            log_error("Failed to get loyalty info", error=e)
            return error_response("Failed to retrieve loyalty information", 500)

    @staticmethod
    def get_ledger() -> Response:
        """
        Get loyalty ledger entries for the current user.
        
        Supports filtering by type and pagination.
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            # Get loyalty account
            loyalty_account = LoyaltyAccount.query.filter_by(user_id=current_user.id).first()
            if not loyalty_account:
                return success_response(
                    "Ledger retrieved successfully",
                    200,
                    {
                        "entries": [],
                        "total": 0,
                        "page": 1,
                        "total_pages": 0,
                    }
                )
            
            # Parse filters
            filters = LoyaltyLedgerFilter.model_validate(request.args.to_dict())
            
            # Build query
            query = LoyaltyLedger.query.filter_by(account_id=loyalty_account.id)
            
            if filters.type:
                query = query.filter_by(type=filters.type)
            
            query = query.order_by(LoyaltyLedger.created_at.desc())
            
            # Paginate
            pagination = query.paginate(
                page=filters.page,
                per_page=filters.per_page,
                error_out=False
            )
            
            return success_response(
                "Ledger retrieved successfully",
                200,
                {
                    "entries": [entry.to_dict() for entry in pagination.items],
                    "total": pagination.total,
                    "page": pagination.page,
                    "total_pages": pagination.pages,
                }
            )
        except Exception as e:
            log_error("Failed to get loyalty ledger", error=e)
            return error_response("Failed to retrieve loyalty ledger", 500)

