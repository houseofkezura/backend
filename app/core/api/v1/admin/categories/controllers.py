"""
Admin category controller.
"""

from __future__ import annotations

from flask import Response, request
from slugify import slugify

from app.extensions import db
from app.models.category import ProductCategory
from app.schemas.categories import CreateCategoryRequest, UpdateCategoryRequest
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class AdminCategoryController:
    """Controller for admin category endpoints."""

    @staticmethod
    def list_categories() -> Response:
        """List categories with pagination and search."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)

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
            log_error("Failed to list categories", error=e)
            return error_response("Failed to retrieve categories", 500)

    @staticmethod
    def get_category(identifier: str) -> Response:
        """Get category by id or slug."""
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
            log_error(f"Failed to get category {identifier}", error=e)
            return error_response("Failed to retrieve category", 500)

    @staticmethod
    def create_category() -> Response:
        """Create a new category."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)

            payload = CreateCategoryRequest.model_validate(request.get_json())

            slug = slugify(payload.name)
            if ProductCategory.query.filter_by(slug=slug).first():
                return error_response("Category with this slug already exists", 409)

            category = ProductCategory(
                name=payload.name,
                alias=payload.alias,
                description=payload.description,
                slug=slug,
                parent_id=payload.parent_id,
            )
            db.session.add(category)
            db.session.commit()

            log_event(f"Category created: {category.id}")
            return success_response("Category created successfully", 201, {"category": category.to_dict(include_children=True)})
        except Exception as e:
            log_error("Failed to create category", error=e)
            db.session.rollback()
            return error_response("Failed to create category", 500)

    @staticmethod
    def update_category(identifier: str) -> Response:
        """Update a category."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)

            payload = UpdateCategoryRequest.model_validate(request.get_json())

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

            if payload.name:
                category.name = payload.name
                category.slug = slugify(payload.name)
            if payload.alias is not None:
                category.alias = payload.alias
            if payload.description is not None:
                category.description = payload.description
            if payload.parent_id is not None:
                category.parent_id = payload.parent_id

            db.session.commit()
            log_event(f"Category updated: {category.id}")
            return success_response("Category updated successfully", 200, {"category": category.to_dict(include_children=True)})
        except Exception as e:
            log_error(f"Failed to update category {identifier}", error=e)
            db.session.rollback()
            return error_response("Failed to update category", 500)

    @staticmethod
    def delete_category(identifier: str) -> Response:
        """Delete a category."""
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)

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

            db.session.delete(category)
            db.session.commit()

            log_event(f"Category deleted: {identifier}")
            return success_response("Category deleted successfully", 200)
        except Exception as e:
            log_error(f"Failed to delete category {identifier}", error=e)
            db.session.rollback()
            return error_response("Failed to delete category", 500)

