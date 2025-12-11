"""
Author: Emmanuel Olowu
Link: https://github.com/zeddyemy
Copyright: © 2024 Emmanuel Olowu <zeddyemy@gmail.com>
License: GNU, see LICENSE for more details.
Package: Kezura
"""
from flask import request, g
from typing import List, Optional, Any, cast
import uuid

from ...models import AppUser, Profile
from quas_utils.misc import generate_random_string
from quas_utils.logging.loggers import console_log


def get_current_user() -> Optional[AppUser]:
    """
    Get the current authenticated user from Flask g context.
    
    This function retrieves the user that was set by Clerk authentication decorators.
    Falls back to legacy JWT/Flask-Login for backward compatibility if needed.
    
    Returns:
        AppUser instance if authenticated, None otherwise.
    """
    # First, try to get from Flask g (set by Clerk decorators)
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user
    
    # Fallback to legacy JWT/Flask-Login for backward compatibility
    if request.path.startswith('/api'):
        # Try legacy JWT (for admin/internal endpoints that haven't migrated yet)
        try:
            from flask_jwt_extended import get_jwt_identity
            jwt_identity = get_jwt_identity()
            
            if jwt_identity:
                user_id = extract_user_id_from_jwt_identity(jwt_identity)
                if user_id:
                    from ...extensions import db
                    return cast(Any, db.session).get(AppUser, user_id)
        except Exception:
            pass
    else:
        # Try Flask-Login for web routes
        try:
            from flask_login import current_user as session_user
            if session_user and session_user.is_authenticated:
                return cast(Optional[AppUser], session_user)
        except Exception:
            pass
    
    return None


def extract_user_id_from_jwt_identity(jwt_identity: Any) -> Optional[uuid.UUID]:
    """
    Extract user ID from JWT identity (legacy support).
    
    Handles both string (UUID as string) and dict (legacy format) for backward compatibility.
    
    Args:
        jwt_identity: JWT identity from get_jwt_identity()
        
    Returns:
        UUID object if valid, None otherwise
    """
    if not jwt_identity:
        return None
    
    # Handle string identity (current format)
    if isinstance(jwt_identity, str):
        try:
            return uuid.UUID(jwt_identity)
        except (ValueError, TypeError):
            return None
    
    # Handle dict identity (legacy format for backward compatibility)
    if isinstance(jwt_identity, dict):
        user_id = jwt_identity.get("user_id")
        if user_id:
            try:
                return uuid.UUID(user_id) if isinstance(user_id, str) else user_id
            except (ValueError, TypeError):
                return None
    
    return None


def get_app_user_info(user_id: Optional[int]):
    """Gets profile details of a particular user"""
    
    if user_id is None:
        user_info: dict = {}
    else:
        app_user = AppUser.query.filter(AppUser.id == user_id).first()
        user_info = app_user.to_dict() if app_user else {}
    
    for key in user_info:
        if user_info[key] is None:
            user_info[key] = "—"
    
    return user_info


def is_user_exist(identifier, field, user=None):
    """
    Checks if a user exists in the database with the given identifier and field.

    Args:
        identifier: The identifier to search for (email or username).
        field: The field to search in ("email" or "username").
        user: An optional user object. If provided, the check excludes the user itself.

    Returns:
        True if the user exists, False otherwise.
    """
    base_query = AppUser.query.filter(getattr(AppUser, field) == identifier)
    if user:
        base_query = base_query.filter(AppUser.id != user.id)
    return base_query.scalar() is not None

def is_username_exist(username, user=None):
    """
    Checks if a username exists in the database, excluding the current user if provided.

    Args:
        username: The username to search for.
        user: An optional user object. If provided, the check excludes the user itself.

    Returns:
        True if the username is already taken, False if it's available.
    """
    base_query = AppUser.query.filter(AppUser.username == username)
    if user:
        # Query the database to check if the username is available, excluding the user's own username
        base_query = base_query.filter(AppUser.id != user.id)
    
    return base_query.scalar() is not None


def is_email_exist(email, user=None):
    """
    Checks if an email address exists in the database, excluding the current user if provided.

    Args:
        email: The email address to search for.
        user: An optional user object. If provided, the check excludes the user itself.

    Returns:
        True if the email address is already taken, False if it's available.
    """
    base_query = AppUser.query.filter(AppUser.email == email)
    if user:
        # Query the database to check if the email is available, excluding the user's own email
        base_query = base_query.filter(AppUser.id != user.id)
    
    return base_query.scalar() is not None


def get_app_user(identifier: str) -> Optional[AppUser]:
    """
    Retrieves a AppUser object from the database based on email or username.

    Args:
        identifier: The email address or username to search for.

    Returns:
        The AppUser object if found, or None if not found.
    """
    
    user = AppUser.query.filter(AppUser.email == identifier).first()
    if user:
        return user
    
    return AppUser.query.filter(AppUser.username == identifier).first()


def generate_referral_code(length=6):
    while True:
        code = generate_random_string(length)
        # Check if the code already exists in the database
        if not referral_code_exists(code):
            return code

def referral_code_exists(code: str) -> bool:
    # `Profile` may not declare a typed `referral_code`; use string attr name for the checker
    profile = Profile.query.filter(getattr(Profile, 'referral_code') == code).first()
    if profile:
        return True
    return False

