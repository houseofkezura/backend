"""
Admin category routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, SecurityScheme, QueryParameter
from app.schemas.response_data import CategoryData, CategoryListData, ValidationErrorData
from app.schemas.categories import CreateCategoryRequest, UpdateCategoryRequest
from app.utils.decorators.auth import roles_required
from .controllers import AdminCategoryController
from . import bp


@bp.get("")
@roles_required("Super Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Categories"],
    summary="List Categories",
    description="List categories with pagination and search. Supports parent_only and parent_id filters.",
    query_params=[
        QueryParameter("page", "integer", required=False, description="Page number", default=1),
        QueryParameter("per_page", "integer", required=False, description="Items per page", default=20),
        QueryParameter("search", "string", required=False, description="Search term"),
        QueryParameter("parent_only", "boolean", required=False, description="Only top-level categories", default=False),
        QueryParameter("parent_id", "integer", required=False, description="Filter by parent category id"),
    ],
    responses={
        "200": CategoryListData,
        "401": None,
        "500": None,
    },
)
def list_categories():
    """List categories."""
    return AdminCategoryController.list_categories()


@bp.get("/<identifier>")
@roles_required("Super Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Categories"],
    summary="Get Category",
    description="Get a category by id or slug.",
    responses={
        "200": CategoryData,
        "401": None,
        "404": None,
        "500": None,
    },
)
def get_category(identifier: str):
    """Get category by id or slug."""
    return AdminCategoryController.get_category(identifier)


@bp.post("")
@roles_required("Super Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Categories"],
    summary="Create Category",
    request_body=CreateCategoryRequest,
    responses={
        "201": CategoryData,
        "400": ValidationErrorData,
        "401": None,
        "409": None,
        "500": None,
    },
)
def create_category():
    """Create category."""
    return AdminCategoryController.create_category()


@bp.put("/<identifier>")
@roles_required("Super Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Categories"],
    summary="Update Category",
    request_body=UpdateCategoryRequest,
    responses={
        "200": CategoryData,
        "400": ValidationErrorData,
        "401": None,
        "404": None,
        "500": None,
    },
)
def update_category(identifier: str):
    """Update category."""
    return AdminCategoryController.update_category(identifier)


@bp.delete("/<identifier>")
@roles_required("Super Admin", "Operations")
@endpoint(
    security=SecurityScheme.ADMIN_BEARER,
    tags=["Admin - Categories"],
    summary="Delete Category",
    responses={
        "200": None,
        "401": None,
        "404": None,
        "500": None,
    },
)
def delete_category(identifier: str):
    """Delete category."""
    return AdminCategoryController.delete_category(identifier)

