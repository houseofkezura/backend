"""
Pydantic schemas for loyalty-related endpoints.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class RedeemPointsRequest(BaseModel):
    """Schema for redeeming loyalty points."""
    points_to_redeem: int = Field(..., ge=500, description="Points to redeem (minimum 500)")


class LoyaltyLedgerFilter(BaseModel):
    """Schema for filtering loyalty ledger entries."""
    type: Optional[str] = Field(None, description="Filter by type (earn, redeem, adjust, expire)")
    page: Optional[int] = Field(1, ge=1, description="Page number")
    per_page: Optional[int] = Field(20, ge=1, le=100, description="Items per page")




