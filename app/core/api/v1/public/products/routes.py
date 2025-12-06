"""
Public product routes.
"""

from __future__ import annotations

from flask_pydantic_spec import Response

from app.extensions.docs import spec, endpoint
from app.schemas.response import SuccessResponse, ErrorResponse
from .controllers import ProductController
from . import bp


@bp.get("")
@endpoint(
    tags=["Products"],
    summary="List Products",
    description="List products with filtering, sorting, and pagination. No authentication required."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_500=ErrorResponse))
def list_products():
    """List products with filters."""
    return ProductController.list_products()


@bp.get("/<slug>")
@endpoint(
    tags=["Products"],
    summary="Get Product by Slug",
    description="Get a single product by slug with all variants. No authentication required."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def get_product(slug: str):
    """Get product by slug."""
    return ProductController.get_product(slug)


@bp.get("/search")
@endpoint(
    tags=["Products"],
    summary="Search Products",
    description="Lightweight search endpoint for autocomplete. No authentication required."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_500=ErrorResponse))
def search_products():
    """Search products."""
    return ProductController.search_products()


@bp.get("/<product_id>/variants")
@endpoint(
    tags=["Products"],
    summary="Get Product Variants",
    description="Get all variants for a product. No authentication required."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_404=ErrorResponse, HTTP_500=ErrorResponse))
def get_product_variants(product_id: str):
    """Get variants for a product."""
    return ProductController.get_product_variants(product_id)

