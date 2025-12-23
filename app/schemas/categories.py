"""
Pydantic schemas for category endpoints.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class CreateCategoryRequest(BaseModel):
    """Schema for creating a category."""
    name: str = Field(..., min_length=1, max_length=50, description="Category name")
    alias: Optional[str] = Field(None, max_length=50, description="Short alias")
    description: Optional[str] = Field(None, max_length=200, description="Description")
    parent_id: Optional[int] = Field(None, description="Parent category ID")


class UpdateCategoryRequest(BaseModel):
    """Schema for updating a category."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    alias: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    parent_id: Optional[int] = Field(None, description="Parent category ID")

