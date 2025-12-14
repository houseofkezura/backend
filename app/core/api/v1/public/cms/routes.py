"""
Public CMS routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint
from app.schemas.response_data import CmsPageData
from .controllers import CmsController
from . import bp


@bp.get("/pages/<slug>")
@endpoint(
    tags=["CMS"],
    summary="Get CMS Page",
    description="Get a published CMS page by slug. No authentication required.",
    responses={
        "200": CmsPageData,
        "404": None,
        "500": None,
    },
)
def get_page(slug: str):
    """Get CMS page by slug."""
    return CmsController.get_page(slug)




