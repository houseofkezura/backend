from __future__ import annotations

from flask import Response, request
import uuid
from email_validator import validate_email, EmailNotValidError

from app.extensions import db
from app.logging import log_error, log_event
from app.models import Role, AppUser, Profile, Address
from app.utils.auth.clerk import create_clerk_user, get_or_create_app_user_from_clerk, AuthenticatedUser
from app.schemas.auth import (
    SignUpRequest, 
    LoginRequest, 
    VerifyEmailRequest,
    ResendCodeRequest,
    ValidateTokenRequest,
    RefreshTokenRequest,
    CheckEmailRequest,
    CheckUsernameRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    VerifyPasswordResetCodeRequest,
    ResetPasswordRequest,
)
from app.utils.emailing import email_service
from app.utils.verification.registration import (
    PendingRegistration,
    store_pending_registration,
    get_pending_registration,
    delete_pending_registration,
    generate_registration_id,
    hash_code,
    increment_attempts,
)
from app.utils.verification.password_recovery import (
    PendingPasswordReset,
    store_pending_password_reset,
    get_pending_password_reset,
    delete_pending_password_reset,
    generate_reset_id,
    hash_reset_code,
    increment_attempts as increment_reset_attempts,
)
from quas_utils.misc import generate_random_number
from app.enums import RoleNames
from app.utils.helpers.user import get_app_user, get_current_user
from quas_utils.api import success_response, error_response
from app.utils.decorators.auth import customer_required


class AuthController:
    @staticmethod
    def sign_up() -> Response:
        """
        Handle user signup by collecting email and referral code, 
        checking for existing users, and sending a verification code.
        """
        payload = SignUpRequest.model_validate(request.get_json())
        email = payload.email.lower()
        firstname = payload.firstname
        lastname = payload.lastname or ''
        username = payload.username
        password = payload.password

        if not email:
            return error_response("email is empty", 400)

        if not firstname:
            return error_response("firstname is empty", 400)

        if not password:
            return error_response("password is empty", 400)

        # Fast email validation without deliverability check for performance
        email_info = validate_email(email, check_deliverability=False)
        email = email_info.normalized

        # Optimized existence checks using scalar queries (faster than first())
        email_exists = db.session.query(AppUser.id).filter_by(email=email).scalar() is not None
        if email_exists:
            return error_response('Email already taken', 409)

        if username:
            username_exists = db.session.query(AppUser.id).filter_by(username=username).scalar() is not None
            if username_exists:
                return error_response('Username already taken', 409)

        # Generate a short code; store only hashed code and password hash in cache
        from quas_utils.misc import generate_random_number
        code = str(generate_random_number(6))
        reg_id = generate_registration_id()
        code_h = hash_code(code, salt=reg_id)

        # Prepare pending record
        # Store plain password temporarily for Clerk user creation (will be cleared after use)
        tmp_user = AppUser()
        tmp_user.set_password(password)
        
        pending = PendingRegistration(
            email=email,
            firstname=firstname,
            lastname=lastname,
            username=username,
            password_hash=tmp_user.password_hash or '',
            password=password,  # Store plain password temporarily for Clerk
            code_hash=code_h,
        )

        store_pending_registration(reg_id, pending, ttl_minutes=15)

        # Send code via email
        email_service.send_verification_code(email, code, expires_minutes=15, context={"firstname": firstname})

        return success_response('Verification code sent successfully', 200, {"reg_id": reg_id})


    @staticmethod
    def verify_email() -> Response:
        """Verify code and finalize user registration using cached pending data."""
        payload = VerifyEmailRequest.model_validate(request.get_json())
        pending = get_pending_registration(payload.reg_id)
        if pending is None:
            return error_response("invalid or expired verification", 400)

        # Limit brute force attempts
        if increment_attempts(payload.reg_id) > 10:
            delete_pending_registration(payload.reg_id)
            return error_response("too many attempts", 429)

        expected = hash_code(str(payload.code), salt=payload.reg_id)
        if pending.code_hash != expected:
            return error_response("invalid code", 400)

        # Re-check uniqueness just before creation using optimized queries
        email_exists = db.session.query(AppUser.id).filter_by(email=pending.email).scalar() is not None
        if email_exists:
            delete_pending_registration(payload.reg_id)
            return error_response('Email already taken', 409)
        
        if pending.username:
            username_exists = db.session.query(AppUser.id).filter_by(username=pending.username).scalar() is not None
            if username_exists:
                delete_pending_registration(payload.reg_id)
                return error_response('Username already taken', 409)

        # Create user
        new_user = AppUser()
        new_user.email = pending.email
        new_user.username = pending.username
        new_user.password_hash = pending.password_hash

        db.session.add(new_user)
        db.session.flush()

        user_profile = Profile()
        user_profile.firstname = pending.firstname
        user_profile.lastname = pending.lastname
        user_profile.user_id = new_user.id

        user_address = Address()
        user_address.user_id = new_user.id

        role = Role.query.filter_by(name=RoleNames.CUSTOMER).first()
        if role:
            from app.models.role import UserRole
            UserRole.assign_role(new_user, role, commit=False)

        db.session.add_all([user_profile, user_address])
        db.session.commit()
        
        # Create Clerk user (use plain password from pending registration)
        plain_password = getattr(pending, 'password', None)
        if plain_password:
            clerk_user_data = create_clerk_user(
                email=new_user.email,
                password=plain_password,
                first_name=pending.firstname,
                last_name=pending.lastname,
                username=pending.username,
            )
            
            if clerk_user_data:
                new_user.clerk_id = clerk_user_data["clerk_id"]
                db.session.commit()
        
        # Clear pending registration (removes plain password from cache)
        delete_pending_registration(payload.reg_id)
        
        return success_response("Email verified and account created. Please log in via Clerk.", 200, {"user_data": new_user.to_dict()})

    @staticmethod
    def resend_verification_code() -> Response:
        """Resend verification code for a pending registration."""
        payload = ResendCodeRequest.model_validate(request.get_json())
        pending = get_pending_registration(payload.reg_id)
        
        if pending is None:
            return error_response("invalid or expired registration", 400)
        
        # Rate limit: allow max 3 resends
        if pending.attempts >= 3:
            return error_response("maximum resend attempts exceeded", 429)
        
        # Generate new code and update cache
        from quas_utils.misc import generate_random_number
        from app.utils.verification.registration import hash_code
        
        new_code = str(generate_random_number(6))
        pending.code_hash = hash_code(new_code, salt=payload.reg_id)
        store_pending_registration(payload.reg_id, pending, ttl_minutes=15)
        
        # Send new code
        email_service.send_verification_code(
            pending.email, 
            new_code, 
            expires_minutes=15, 
            context={"firstname": pending.firstname}
        )
        
        return success_response("Verification code resent", 200)

    @staticmethod
    def validate_token() -> Response:
        """
        Validate Clerk token.
        
        This endpoint validates a Clerk session/JWT token and returns user info.
        Clerk handles token refresh automatically, so this is mainly for validation.
        """
        from app.utils.decorators.auth import get_auth_token
        from app.utils.auth.clerk import get_clerk_user_from_token
        
        token = get_auth_token()
        if not token:
            return error_response("Missing authentication token", 401)
        
        clerk_user = get_clerk_user_from_token(token)
        if not clerk_user:
            return error_response("Invalid or expired token", 401)
        
        app_user = get_or_create_app_user_from_clerk(clerk_user)
        if not app_user:
            return error_response("Failed to load user", 500)
        
        return success_response("Token is valid", 200, {
            "valid": True,
            "user_data": app_user.to_dict()
        })

    @staticmethod 
    def refresh_token() -> Response:
        """
        Token refresh is handled by Clerk automatically.
        
        This endpoint is kept for backward compatibility but returns a message
        directing clients to use Clerk's refresh mechanism.
        """
        return success_response(
            "Token refresh is handled by Clerk. Use Clerk's refresh endpoint.", 
            200,
            {"message": "Clerk handles token refresh automatically"}
        )

    @staticmethod
    def check_email_availability() -> Response:
        """Check if an email is already taken."""
        payload = CheckEmailRequest.model_validate(request.get_json())
        
        try:
            # Validate and normalize email
            email_info = validate_email(payload.email, check_deliverability=False)
            normalized_email = email_info.normalized
        except EmailNotValidError:
            return error_response("invalid email format", 400)
        
        # Fast existence check using scalar query
        exists = db.session.query(AppUser.id).filter_by(email=normalized_email).scalar() is not None
        
        return success_response("Email availability checked", 200, {
            "email": normalized_email,
            "available": not exists
        })

    @staticmethod  
    def check_username_availability() -> Response:
        """Check if a username is already taken."""
        payload = CheckUsernameRequest.model_validate(request.get_json())
        username = payload.username.strip()
        
        if not username:
            return error_response("username cannot be empty", 400)
        
        # Fast existence check using scalar query
        exists = db.session.query(AppUser.id).filter_by(username=username).scalar() is not None
        
        return success_response("Username availability checked", 200, {
            "username": username,
            "available": not exists
        })


    @staticmethod
    def login() -> Response:
        """
        Login is handled by Clerk.
        
        This endpoint is deprecated. Clients should use Clerk's authentication
        endpoints directly. This is kept for backward compatibility.
        """
        return error_response(
            "Login is handled by Clerk. Please use Clerk's authentication endpoints.", 
            410  # Gone status
        )
    
    @staticmethod
    def change_password() -> Response:
        """
        Change password for authenticated user.
        
        Requires current password verification.
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            payload = ChangePasswordRequest.model_validate(request.get_json())
            
            # Verify current password
            if not current_user.check_password(payload.current_password):
                return error_response("Current password is incorrect", 400)
            
            # Set new password
            current_user.set_password(payload.new_password)
            # Mark that user has updated their default password
            current_user.has_updated_default_password = True
            db.session.commit()
            
            log_event("Password changed", {"user_id": str(current_user.id)})
            
            return success_response("Password changed successfully", 200)
        except Exception as e:
            log_error("Failed to change password", error=e)
            db.session.rollback()
            return error_response("Failed to change password", 500)
    
    @staticmethod
    def forgot_password() -> Response:
        """
        Request password reset code.
        
        Sends a verification code to the user's email.
        """
        try:
            payload = ForgotPasswordRequest.model_validate(request.get_json())
            email = payload.email.lower().strip()
            
            # Check if user exists
            user = AppUser.query.filter_by(email=email).first()
            if not user:
                # Don't reveal if email exists or not for security
                return success_response("If the email exists, a reset code has been sent", 200)
            
            # Generate reset ID and code
            reset_id = generate_reset_id()
            code = str(generate_random_number(6))
            code_hash = hash_reset_code(code, salt=reset_id)
            
            log_event("Reset ID: ", {"reset_id": reset_id})
            log_event("Code: ", {"code": code})
            log_event("Code hash: ", {"code_hash": code_hash})
            
            # Store pending reset
            pending = PendingPasswordReset(
                email=email,
                code_hash=code_hash,
                attempts=0
            )
            store_pending_password_reset(reset_id, pending, ttl_minutes=15)
            
            # Send verification code email
            email_service.send_verification_code(
                to=email,
                code=code,
                expires_minutes=15,
                context={"purpose": "password reset"}
            )
            
            log_event("Password reset code sent", {"email": email, "reset_id": reset_id})
            
            return success_response("If the email exists, a reset code has been sent", 200, {
                "reset_id": reset_id
            })
        except Exception as e:
            log_error("Failed to send password reset code", error=e)
            return error_response("Failed to send reset code", 500)
    
    @staticmethod
    def verify_password_reset_code() -> Response:
        """
        Verify password reset code.
        
        Validates the code sent to user's email.
        """
        try:
            payload = VerifyPasswordResetCodeRequest.model_validate(request.get_json())
            reset_id = payload.reset_id
            code = payload.code
            
            pending = get_pending_password_reset(reset_id)
            if pending is None:
                return error_response("Invalid or expired reset code", 400)
            
            # Limit brute force attempts
            if increment_reset_attempts(reset_id) > 10:
                delete_pending_password_reset(reset_id)
                return error_response("Too many attempts", 429)
            
            # Verify code
            expected = hash_reset_code(code, salt=reset_id)
            if pending.code_hash != expected:
                return error_response("Invalid code", 400)
            
            # Code is valid
            return success_response("Code verified successfully", 200, {
                "reset_id": reset_id,
                "verified": True
            })
        except Exception as e:
            log_error("Failed to verify password reset code", error=e)
            return error_response("Failed to verify code", 500)
    
    @staticmethod
    def reset_password() -> Response:
        """
        Reset password with verified code.
        
        Resets user's password after code verification.
        """
        try:
            payload = ResetPasswordRequest.model_validate(request.get_json())
            reset_id = payload.reset_id
            code = payload.code
            new_password = payload.new_password
            
            # Verify code
            pending = get_pending_password_reset(reset_id)
            if pending is None:
                return error_response("Invalid or expired reset code", 400)
            
            expected = hash_reset_code(code, salt=reset_id)
            if pending.code_hash != expected:
                return error_response("Invalid code", 400)
            
            # Find user by email
            user = AppUser.query.filter_by(email=pending.email).first()
            if not user:
                delete_pending_password_reset(reset_id)
                return error_response("User not found", 404)
            
            # Update password
            user.set_password(new_password)
            # Mark that user has updated their default password
            user.has_updated_default_password = True
            db.session.commit()
            
            # Delete reset record
            delete_pending_password_reset(reset_id)
            
            log_event("Password reset completed", {"user_id": str(user.id), "email": pending.email})
            
            return success_response("Password reset successfully", 200)
        except Exception as e:
            log_error("Failed to reset password", error=e)
            db.session.rollback()
            return error_response("Failed to reset password", 500)

