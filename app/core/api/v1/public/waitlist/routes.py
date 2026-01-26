"""
Public waitlist routes.
"""

from __future__ import annotations

from app.extensions.docs import endpoint
from app.schemas.response_data import WaitlistEntryData, WaitlistCheckData, ValidationErrorData
from app.schemas.waitlist import CreateWaitlistEntryRequest
from .controllers import WaitlistController
from . import bp


@bp.post("/join")
@endpoint(
    request_body=CreateWaitlistEntryRequest,
    tags=["Waitlist"],
    summary="Join Waitlist",
    description="Join the waitlist. No authentication required.",
    responses={
        "201": WaitlistEntryData,
        "400": ValidationErrorData,
        "409": None,
        "500": None,
    },
)
def join_waitlist():
    """Join the waitlist."""
    return WaitlistController.join_waitlist()


@bp.get("/check")
@endpoint(
    tags=["Waitlist"],
    summary="Check Waitlist Status",
    description="Check if an email is on the waitlist. No authentication required.",
    responses={
        "200": WaitlistCheckData,
        "400": ValidationErrorData,
        "500": None,
    },
)
def check_status():
    """Check waitlist status for an email."""
    return WaitlistController.check_status()
