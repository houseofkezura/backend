"""
Pydantic schemas for admin endpoints.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class LoyaltyAdjustRequest(BaseModel):
    """Schema for adjusting loyalty points."""
    points: int = Field(..., description="Points delta (positive or negative)")
    reason: Optional[str] = Field("Manual adjustment by admin", description="Reason for adjustment")


class StaffCreateRequest(BaseModel):
    """Schema for creating CRM staff."""
    name: str = Field(..., min_length=1)
    staff_code: str = Field(..., min_length=1)
    contact: Optional[str] = None
    role: Optional[str] = None


class CmsPageCreateRequest(BaseModel):
    """Schema for creating CMS page."""
    slug: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    published: bool = False


class CmsPageUpdateRequest(BaseModel):
    """Schema for updating CMS page."""
    slug: Optional[str] = Field(None, min_length=1)
    title: Optional[str] = Field(None, min_length=1)
    content: Optional[str] = Field(None, min_length=1)
    published: Optional[bool] = None


class B2BUpdateStatusRequest(BaseModel):
    """Schema for updating B2B inquiry status."""
    status: Optional[str] = Field(None, min_length=1)
    note: Optional[str] = None


class OrderStatusUpdateRequest(BaseModel):
    """Schema for updating order status."""
    status: str = Field(..., min_length=1)
    notes: Optional[str] = None


class RevampStatusUpdateRequest(BaseModel):
    """Schema for updating revamp request status."""
    status: Optional[str] = Field(None, min_length=1)
    assigned_to: Optional[str] = Field(None, description="CRM staff ID")


class AssignRoleRequest(BaseModel):
    """Schema for assigning/revoking a role."""
    role: str = Field(..., min_length=1)





