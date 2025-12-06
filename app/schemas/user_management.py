"""Pydantic schemas for user management endpoints."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID


class UserSummary(BaseModel):
    """Schema for user summary in list responses."""

    id: UUID
    username: Optional[str] = None
    email: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    date_joined: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    is_active: bool = True


class UserDetails(BaseModel):
    """Schema for detailed user information."""

    id: UUID
    username: Optional[str] = None
    email: Optional[str] = None
    date_joined: Optional[str] = None
    profile: dict = Field(default_factory=dict)
    address: dict = Field(default_factory=dict)
    wallet: dict = Field(default_factory=dict)
    roles: List[str] = Field(default_factory=list)
    is_active: bool = True


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""

    users: List[UserSummary]
    total: int
    page: int
    per_page: int
    total_pages: int


class UserStatsResponse(BaseModel):
    """Schema for user statistics response."""

    total_users: int
    active_users: int
    inactive_users: int
    admin_users: int
    organizer_users: int
    participant_users: int
    visitor_users: int
    recent_registrations: int


class UpdateUserRolesRequest(BaseModel):
    """Schema for updating user roles."""

    roles_to_add: List[str] = Field(default_factory=list, description="List of role names to add")
    roles_to_remove: List[str] = Field(default_factory=list, description="List of role names to remove")


class UpdateUserStatusRequest(BaseModel):
    """Schema for updating user status."""

    is_active: bool = Field(description="Whether the user account should be active")


class UpdateUserProfileRequest(BaseModel):
    """Schema for updating user profile."""

    firstname: Optional[str] = Field(None, description="User's first name")
    lastname: Optional[str] = Field(None, description="User's last name")
    phone: Optional[str] = Field(None, description="User's phone number")
    gender: Optional[str] = Field(None, description="User's gender")
    enrollment_no: Optional[str] = Field(None, description="User's enrollment number")
    department: Optional[str] = Field(None, description="User's department")


class UpdateUserAddressRequest(BaseModel):
    """Schema for updating user address."""

    country: Optional[str] = Field(None, description="User's country")
    state: Optional[str] = Field(None, description="User's state/province")


