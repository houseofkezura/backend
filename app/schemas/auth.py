"""Pydantic schemas for auth endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class SignUpRequest(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    firstname: str = Field(min_length=1)
    lastname: str | None = None
    username: str | None = None
    password: str = Field(min_length=6)


class LoginRequest(BaseModel):
    """Schema for user login."""

    email_username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class AvailabilityResponse(BaseModel):
    """Response data for availability checks."""

    value: str
    available: bool


class ResetCodeResponse(BaseModel):
    """Response data for password reset code delivery."""

    reset_id: Optional[str] = None


class ResetCodeVerificationResponse(BaseModel):
    """Response data for verifying a reset code."""

    reset_id: str
    verified: bool = True


class RefreshInfoResponse(BaseModel):
    """Response data for refresh-token guidance."""

    message: str


class VerifyEmailRequest(BaseModel):
    """Schema for email verification."""

    reg_id: str = Field(min_length=8)
    code: str = Field(min_length=4, max_length=8)


class ResendCodeRequest(BaseModel):
    """Schema for resending verification code."""

    reg_id: str = Field(min_length=8)


class ValidateTokenRequest(BaseModel):
    """Schema for token validation."""

    token: str = Field(min_length=1)


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh."""

    token: str = Field(min_length=1)


class CheckEmailRequest(BaseModel):
    """Schema for email availability check."""

    email: EmailStr


class CheckUsernameRequest(BaseModel):
    """Schema for username availability check."""

    username: str = Field(min_length=1)


class ChangePasswordRequest(BaseModel):
    """Schema for changing password (authenticated user)."""

    current_password: str = Field(min_length=1, description="Current password")
    new_password: str = Field(min_length=6, description="New password (minimum 6 characters)")


class VerifyPasswordResetCodeRequest(BaseModel):
    """Schema for verifying password reset code."""

    reset_id: str = Field(min_length=8, description="Password reset identifier")
    code: str = Field(min_length=4, max_length=8, description="Verification code")


class ForgotPasswordRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr


class ValidateResetTokenRequest(BaseModel):
    """Schema for password reset token validation."""

    token: str = Field(min_length=1)


class ResetPasswordRequest(BaseModel):
    """Schema for password reset with code."""

    reset_id: str = Field(min_length=8, description="Password reset identifier")
    code: str = Field(min_length=4, max_length=8, description="Verification code")
    new_password: str = Field(min_length=6, description="New password (minimum 6 characters)")
