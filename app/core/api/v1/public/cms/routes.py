"""
Public CMS routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint
from app.schemas.response import SuccessResp, NotFoundResp, ServerErrorResp
from .controllers import CmsController
from . import bp


@bp.get("/pages/<slug>")
@endpoint(
    tags=["CMS"],
    summary="Get CMS Page",
    description="Get a published CMS page by slug. No authentication required.",
    responses={
        "200": SuccessResp,
        "404": NotFoundResp,
        "500": ServerErrorResp,
    },
)
def get_page(slug: str):
    """Get CMS page by slug."""
    return CmsController.get_page(slug)




