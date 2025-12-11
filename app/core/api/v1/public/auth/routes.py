from __future__ import annotations
from .controllers import AuthController
from app.extensions.docs import endpoint, SecurityScheme
from app.schemas.response import (
    ApiResp,
    SuccessResp,
    BadRequestResp,
    UnauthorizedResp,
    ConflictResp,
    TooManyRequestsResp,
    NotFoundResp,
)
from app.schemas.auth import (
    VerifyEmailRequest, 
    SignUpRequest, 
    LoginRequest,
    ResendCodeRequest,
    ValidateTokenRequest,
    CheckEmailRequest,
    CheckUsernameRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    VerifyPasswordResetCodeRequest,
    ResetPasswordRequest,
)

from . import bp


@bp.post("/login")
@endpoint(
    request_body=LoginRequest,
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "401": UnauthorizedResp,
    },
    tags=["Authentication"],
    summary="User Login",
    description="Authenticate user with email/username and password to receive accesstoken"
)
def login():
    """Authenticate and return access token."""
    return AuthController.login()

@bp.post("/signup")
@endpoint(
    request_body=SignUpRequest,
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "409": ConflictResp,
    },
    tags=["Authentication"],
    summary="User Registration",
    description="Create new user account and send email verification code"
    )
def sign_up():
    """Create a new account."""
    return AuthController.sign_up()


@bp.post("/verify-email")
@endpoint(
    request_body=VerifyEmailRequest,
    tags=["Authentication"],
    summary="Email Verification",
    description="Verify email with code to complete registration",
    responses={
        "200": ApiResp,
        "400": BadRequestResp,
        "409": ConflictResp,
    }
    )
def verify_email():
    """Verify emailed code and finalize registration."""
    return AuthController.verify_email()


@bp.post("/resend-code")
@endpoint(
    request_body=ResendCodeRequest,
    tags=["Authentication"],
    summary="Resend Verification Code",
    description="Resend email verification code for pending registration",
    responses={
        "200": ApiResp,
        "400": BadRequestResp,
        "429": TooManyRequestsResp,
    }
    )
def resend_verification_code():
    """Resend verification code for pending registration."""
    return AuthController.resend_verification_code()


@bp.post("/validate-token")
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Authentication"],
    summary="Validate JWT Token",
    description="Check if a JWT token is valid and not expired",
    responses={"200": ApiResp}
    )
def validate_token():
    """Validate if a JWT token is valid and not expired."""
    return AuthController.validate_token()


@bp.post("/refresh-token")
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Authentication"],
    summary="Refresh Access Token",
    description="Generate new access token using existing valid token",
    responses={
        "200": ApiResp,
        "401": UnauthorizedResp,
        "404": NotFoundResp,
    }
    )
def refresh_token():
    """Refresh an access token."""
    return AuthController.refresh_token()


@bp.post("/check-email")
@endpoint(
    request_body=CheckEmailRequest,
    tags=["Utilities"],
    summary="Check Email Availability",
    responses={"200": ApiResp, "400": BadRequestResp},
)
def check_email_availability():
    """Check if an email is already taken."""
    return AuthController.check_email_availability()


@bp.post("/check-username")
@endpoint(
    request_body=CheckUsernameRequest,
    tags=["Utilities"],
    summary="Check Username Availability",
    responses={"200": ApiResp, "400": BadRequestResp},
)
def check_username_availability():
    """Check if a username is already taken."""
    return AuthController.check_username_availability()


@bp.post("/change-password")
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=ChangePasswordRequest,
    tags=["Authentication"],
    summary="Change Password",
    description="Change password for authenticated user (requires current password)",
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "401": UnauthorizedResp,
    }
)
def change_password():
    """Change password for authenticated user."""
    return AuthController.change_password()


@bp.post("/forgot-password")
@endpoint(
    request_body=ForgotPasswordRequest,
    tags=["Authentication"],
    summary="Request Password Reset",
    description="Request password reset code to be sent to email",
    responses={"200": SuccessResp, "400": BadRequestResp}
)
def forgot_password():
    """Request password reset code."""
    return AuthController.forgot_password()


@bp.post("/verify-password-reset-code")
@endpoint(
    request_body=VerifyPasswordResetCodeRequest,
    tags=["Authentication"],
    summary="Verify Password Reset Code",
    description="Verify the password reset code sent to email",
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "429": TooManyRequestsResp,
    }
)
def verify_password_reset_code():
    """Verify password reset code."""
    return AuthController.verify_password_reset_code()


@bp.post("/reset-password")
@endpoint(
    request_body=ResetPasswordRequest,
    tags=["Authentication"],
    summary="Reset Password",
    description="Reset password using verified reset code",
    responses={
        "200": SuccessResp,
        "400": BadRequestResp,
        "404": NotFoundResp,
    }
)
def reset_password():
    """Reset password with verified code."""
    return AuthController.reset_password()