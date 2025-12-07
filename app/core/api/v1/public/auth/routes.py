from __future__ import annotations
from flask_pydantic_spec import Response

from .controllers import AuthController
from app.extensions.docs import spec, endpoint, SecurityScheme
from app.utils.decorators.auth import customer_required
from app.schemas.response import ApiResponse, SuccessResponse, ErrorResponse
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
    tags=["Authentication"],
    summary="User Login",
    description="Authenticate user with email/username and password to receive accesstoken"
    )
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse))
def login():
    """Authenticate and return access token."""
    return AuthController.login()

@bp.post("/signup")
@endpoint(
    request_body=SignUpRequest,
    tags=["Authentication"],
    summary="User Registration",
    description="Create new user account and send email verification code"
    )
@spec.validate(resp=Response(HTTP_200=ApiResponse, HTTP_400=ErrorResponse, HTTP_409=ErrorResponse))
def sign_up():
    """Create a new account."""
    return AuthController.sign_up()


@bp.post("/verify-email")
@endpoint(
    request_body=VerifyEmailRequest,
    tags=["Authentication"],
    summary="Email Verification",
    description="Verify email with code to complete registration"
    )
@spec.validate(resp=Response(HTTP_200=ApiResponse, HTTP_400=ErrorResponse, HTTP_409=ErrorResponse))
def verify_email():
    """Verify emailed code and finalize registration."""
    return AuthController.verify_email()


@bp.post("/resend-code")
@endpoint(
    request_body=ResendCodeRequest,
    tags=["Authentication"],
    summary="Resend Verification Code",
    description="Resend email verification code for pending registration"
    )
@spec.validate(resp=Response(HTTP_200=ApiResponse, HTTP_400=ErrorResponse, HTTP_429=ErrorResponse))
def resend_verification_code():
    """Resend verification code for pending registration."""
    return AuthController.resend_verification_code()


@bp.post("/validate-token")
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Authentication"],
    summary="Validate Clerk Token",
    description="Check if a Clerk token is valid and return user info"
    )
@spec.validate(resp=Response(HTTP_200=ApiResponse, HTTP_401=ErrorResponse))
def validate_token():
    """Validate Clerk token and return user info."""
    return AuthController.validate_token()


@bp.post("/refresh-token")
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Authentication"],
    summary="Refresh Token (Info)",
    description="Token refresh is handled by Clerk automatically"
    )
@spec.validate(resp=Response(HTTP_200=ApiResponse))
def refresh_token():
    """Info: Token refresh is handled by Clerk."""
    return AuthController.refresh_token()


@bp.post("/check-email")
@endpoint(
    request_body=CheckEmailRequest,
    tags=["Utilities"],
    summary="Check Email Availability",
)
@spec.validate(resp=Response(HTTP_200=ApiResponse, HTTP_400=ErrorResponse))
def check_email_availability():
    """Check if an email is already taken."""
    return AuthController.check_email_availability()


@bp.post("/check-username")
@endpoint(
    request_body=CheckUsernameRequest,
    tags=["Utilities"],
    summary="Check Username Availability",
)
@spec.validate(resp=Response(HTTP_200=ApiResponse, HTTP_400=ErrorResponse))
def check_username_availability():
    """Check if a username is already taken."""
    return AuthController.check_username_availability()


@bp.post("/change-password")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    request_body=ChangePasswordRequest,
    tags=["Authentication"],
    summary="Change Password",
    description="Change password for authenticated user (requires current password). Note: Password changes should ideally be handled by Clerk."
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_401=ErrorResponse))
def change_password():
    """Change password for authenticated user."""
    return AuthController.change_password()


@bp.post("/forgot-password")
@endpoint(
    request_body=ForgotPasswordRequest,
    tags=["Authentication"],
    summary="Request Password Reset",
    description="Request password reset code to be sent to email"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse))
def forgot_password():
    """Request password reset code."""
    return AuthController.forgot_password()


@bp.post("/verify-password-reset-code")
@endpoint(
    request_body=VerifyPasswordResetCodeRequest,
    tags=["Authentication"],
    summary="Verify Password Reset Code",
    description="Verify the password reset code sent to email"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_429=ErrorResponse))
def verify_password_reset_code():
    """Verify password reset code."""
    return AuthController.verify_password_reset_code()


@bp.post("/reset-password")
@endpoint(
    request_body=ResetPasswordRequest,
    tags=["Authentication"],
    summary="Reset Password",
    description="Reset password using verified reset code"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_400=ErrorResponse, HTTP_404=ErrorResponse))
def reset_password():
    """Reset password with verified code."""
    return AuthController.reset_password()


@bp.get("/me")
@customer_required
@endpoint(
    security=SecurityScheme.PUBLIC_BEARER,
    tags=["Authentication"],
    summary="Get Current User",
    description="Get current authenticated user information (Clerk-based)"
)
@spec.validate(resp=Response(HTTP_200=SuccessResponse, HTTP_401=ErrorResponse))
def get_me():
    """Get current user information."""
    from app.utils.helpers.user import get_current_user
    from app.utils.helpers.api_response import success_response, error_response
    from flask import g
    
    current_user = get_current_user()
    if not current_user:
        return error_response("Unauthorized", 401)
    
    user_data = current_user.to_dict()
    
    # Include loyalty information
    from app.models.loyalty import LoyaltyAccount
    loyalty_account = LoyaltyAccount.query.filter_by(user_id=current_user.id).first()
    if loyalty_account:
        user_data["loyalty"] = loyalty_account.to_dict()
    
    return success_response(
        "User information retrieved successfully",
        200,
        {"user": user_data}
    )