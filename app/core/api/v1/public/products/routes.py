"""
Public product routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint
from app.schemas.response import SuccessResp, NotFoundResp, ServerErrorResp
from .controllers import ProductController
from . import bp


@bp.get("")
@endpoint(
    tags=["Products"],
    summary="List Products",
    description="List products with filtering, sorting, and pagination. No authentication required.",
    responses={
        "200": SuccessResp,
        "500": ServerErrorResp,
    },
)
def list_products():
    """List products with filters."""
    return ProductController.list_products()


@bp.get("/<slug>")
@endpoint(
    tags=["Products"],
    summary="Get Product by Slug",
    description="Get a single product by slug with all variants. No authentication required.",
    responses={
        "200": SuccessResp,
        "404": NotFoundResp,
        "500": ServerErrorResp,
    },
)
def get_product(slug: str):
    """Get product by slug."""
    return ProductController.get_product(slug)


@bp.get("/search")
@endpoint(
    tags=["Products"],
    summary="Search Products",
    description="Lightweight search endpoint for autocomplete. No authentication required.",
    responses={
        "200": SuccessResp,
        "500": ServerErrorResp,
    },
)
def search_products():
    """Search products."""
    return ProductController.search_products()


@bp.get("/<product_id>/variants")
@endpoint(
    tags=["Products"],
    summary="Get Product Variants",
    description="Get all variants for a product. No authentication required.",
    responses={
        "200": SuccessResp,
        "404": NotFoundResp,
        "500": ServerErrorResp,
    },
)
def get_product_variants(product_id: str):
    """Get variants for a product."""
    return ProductController.get_product_variants(product_id)




