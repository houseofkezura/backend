"""
Admin authentication controller.
"""

from __future__ import annotations

from flask import Response
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.utils.decorators.auth import roles_required


class AdminAuthController:
    """Controller for admin authentication endpoints."""

    @staticmethod
    @roles_required("Super Admin", "Admin", "Operations", "CRM Manager", "Finance", "Support")
    def verify() -> Response:
        """
        Verify admin authentication and return user info.
        
        This endpoint validates that the current user has admin privileges.
        """
        current_user = get_current_user()
        if not current_user:
            return error_response("Unauthorized", 401)
        
        user_data = current_user.to_dict()
        
        return success_response(
            "Admin authentication verified",
            200,
            {"user": user_data}
        )






