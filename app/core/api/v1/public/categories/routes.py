"""
Public category routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint, QueryParameter
from app.schemas.response_data import CategoryData, CategoryListData
from .controllers import PublicCategoryController
from . import bp


@bp.get("")
@endpoint(
    tags=["Categories"],
    summary="List Categories",
    description="List categories (public). Supports pagination, search, parent_only, and parent_id filters.",
    query_params=[
        QueryParameter("page", "integer", required=False, description="Page number", default=1),
        QueryParameter("per_page", "integer", required=False, description="Items per page", default=20),
        QueryParameter("search", "string", required=False, description="Search term"),
        QueryParameter("parent_only", "boolean", required=False, description="Only top-level categories", default=False),
        QueryParameter("parent_id", "integer", required=False, description="Filter by parent category id"),
    ],
    responses={
        "200": CategoryListData,
        "500": None,
    },
)
def list_categories():
    """List categories."""
    return PublicCategoryController.list_categories()


@bp.get("/<identifier>")
@endpoint(
    tags=["Categories"],
    summary="Get Category",
    description="Get category by id or slug (public).",
    responses={
        "200": CategoryData,
        "404": None,
        "500": None,
    },
)
def get_category(identifier: str):
    """Get category by id or slug."""
    return PublicCategoryController.get_category(identifier)

