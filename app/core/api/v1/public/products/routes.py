"""
Public product routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint
from app.schemas.response_data import (
    ProductListData,
    ProductData,
    ProductSearchData,
    ProductVariantsData,
)
from .controllers import ProductController
from . import bp


@bp.get("")
@endpoint(
    tags=["Products"],
    summary="List Products",
    description="List products with filters (category, launch_status, search), sorting, and pagination. Public endpoint.",
    responses={
        "200": ProductListData
    },
)
def list_products():
    """List products with filters."""
    return ProductController.list_products()


@bp.get("/<slug>")
@endpoint(
    tags=["Products"],
    summary="Get Product by Slug",
    description="Get a single product by slug with variants and metadata. Public.",
    responses={
        "200": ProductData,
        "404": None,
        "500": None,
    },
)
def get_product(slug: str):
    """Get product by slug."""
    return ProductController.get_product(slug)


@bp.get("/search")
@endpoint(
    tags=["Products"],
    summary="Search Products",
    description="Lightweight search for autocomplete. Public.",
    responses={
        "200": ProductSearchData,
        "500": None,
    },
)
def search_products():
    """Search products."""
    return ProductController.search_products()


@bp.get("/<product_id>/variants")
@endpoint(
    tags=["Products"],
    summary="Get Product Variants",
    description="Get all variants for a product by product_id. Public.",
    responses={
        "200": ProductVariantsData,
        "404": None,
        "500": None,
    },
)
def get_product_variants(product_id: str):
    """Get variants for a product."""
    return ProductController.get_product_variants(product_id)




