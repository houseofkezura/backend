"""
CMS controller for public content endpoints.
"""

from __future__ import annotations

from flask import Response

from app.extensions import db
from app.models.cms import CmsPage
from quas_utils.api import success_response, error_response
from app.logging import log_error


class CmsController:
    """Controller for public CMS endpoints."""

    @staticmethod
    def get_page(slug: str) -> Response:
        """
        Get a CMS page by slug.
        
        Public endpoint - no authentication required.
        
        Args:
            slug: Page slug
        """
        try:
            page = CmsPage.query.filter_by(slug=slug, published=True).first()
            
            if not page:
                return error_response("Page not found", 404)
            
            return success_response(
                "Page retrieved successfully",
                200,
                {"page": page.to_dict()}
            )
        except Exception as e:
            log_error(f"Failed to get CMS page {slug}", error=e)
            return error_response("Failed to retrieve page", 500)





