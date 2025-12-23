"""
Public category controller.
"""

from __future__ import annotations

from flask import Response, request

from app.models.category import ProductCategory
from quas_utils.api import success_response, error_response
from app.logging import log_error


class PublicCategoryController:
    """Controller for public category endpoints."""

    @staticmethod
    def list_categories() -> Response:
        """List categories (public)."""
        try:
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 20, type=int)
            search = request.args.get("search", type=str)
            parent_only = request.args.get("parent_only", "false").lower() == "true"
            parent_id = request.args.get("parent_id", type=int)

            query = ProductCategory.query
            if parent_only:
                query = query.filter(ProductCategory.parent_id == None)
            if parent_id:
                query = query.filter(ProductCategory.parent_id == parent_id)
            if search:
                query = ProductCategory.add_search_filters(query, search)

            pagination = query.order_by(ProductCategory.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
            categories = [c.to_dict(include_children=True) for c in pagination.items]

            return success_response(
                "Categories retrieved successfully",
                200,
                {
                    "categories": categories,
                    "pagination": {
                        "page": pagination.page,
                        "per_page": pagination.per_page,
                        "total": pagination.total,
                        "pages": pagination.pages,
                    },
                },
            )
        except Exception as e:
            log_error("Failed to list categories (public)", error=e)
            return error_response("Failed to retrieve categories", 500)

    @staticmethod
    def get_category(identifier: str) -> Response:
        """Get category by id or slug (public)."""
        try:
            category = ProductCategory.query.filter(
                (ProductCategory.slug == identifier) | (ProductCategory.id == identifier)
            ).first()
            if not category:
                try:
                    category = ProductCategory.query.get(int(identifier))
                except Exception:
                    category = None
            if not category:
                return error_response("Category not found", 404)
            return success_response("Category retrieved successfully", 200, {"category": category.to_dict(include_children=True)})
        except Exception as e:
            log_error(f"Failed to get category (public) {identifier}", error=e)
            return error_response("Failed to retrieve category", 500)

