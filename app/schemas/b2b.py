"""
Pydantic schemas for B2B inquiry endpoints.
"""

from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


class CreateB2BInquiryRequest(BaseModel):
    """Schema for creating a B2B inquiry."""
    business_name: str = Field(..., min_length=1, max_length=255, description="Business name")
    business_type: Optional[str] = Field(None, description="Business type (Salon, Retailer, etc.)")
    contact_name: str = Field(..., min_length=1, max_length=255, description="Contact person name")
    email: EmailStr = Field(..., description="Contact email")
    phone: str = Field(..., min_length=1, description="Contact phone")
    country: str = Field(..., min_length=2, max_length=100, description="Country")
    expected_volume: Optional[str] = Field(None, description="Expected monthly purchase volume")
    product_categories: Optional[List[str]] = Field(None, description="Product categories of interest")
    note: Optional[str] = Field(None, description="Additional message")






