'''
This module defines authentication and authorization decorators for the Flask application.

Used for handling Clerk-based authentication and role-based access control.
The decorators validate Clerk tokens and enforce RBAC using roles stored in the database.

@author: Emmanuel Olowu
@link: https://github.com/zeddyemy
'''
from functools import wraps
from typing import Callable, TypeVar, Any, ParamSpec, cast, Optional
from flask import g, request, Response
from flask.typing import ResponseReturnValue

from app.models.user import AppUser
from app.models.role import UserRole as TUserRole
from app.extensions import db
from ..helpers.loggers import console_log
from ..helpers.api_response import error_response
from ..helpers.roles import normalize_role
from ..auth.clerk import get_clerk_user_from_token, get_or_create_app_user_from_clerk

# Define type variables for better type hinting
P = ParamSpec('P')
R = TypeVar('R')


def get_auth_token() -> Optional[str]:
    """
    Extract Bearer token from Authorization header.
    
    Returns:
        Token string if found, None otherwise.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return None


def customer_required(fn: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to require Clerk authentication for customer endpoints.
    
    Validates Clerk token, loads/creates AppUser, and attaches to g.current_user.
    
    Args:
        fn: The function to decorate.
        
    Returns:
        Decorated function that requires authentication.
    """
    @wraps(fn)
    def _impl(*args: P.args, **kwargs: P.kwargs) -> R:
        token = get_auth_token()
        if not token:
            return cast(R, error_response("Missing authentication token", 401))
        
        clerk_user = get_clerk_user_from_token(token)
        if not clerk_user:
            return cast(R, error_response("Invalid or expired token", 401))
        
        app_user = get_or_create_app_user_from_clerk(clerk_user)
        if not app_user:
            return cast(R, error_response("Failed to load user", 500))
        
        # Attach to Flask g for access in views
        g.current_user = app_user
        
        return fn(*args, **kwargs)
    
    return cast(Callable[P, R], _impl)


def public_auth_required(fn: Callable[P, R]) -> Callable[P, R]:
    """
    Alias for customer_required for public API endpoints.
    
    Args:
        fn: The function to decorate.
        
    Returns:
        Decorated function that requires authentication.
    """
    return customer_required(fn)


def roles_required(*required_roles: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to ensure that the current user has all of the specified roles.

    This decorator will return a 403 error if the current user does not have
    all of the roles specified in `required_roles`. Requires Clerk authentication.

    Args:
        *required_roles (str): The required roles to access the route.

    Returns:
        function: The decorated function.

    Raises:
        HTTPException: A 403 error if the current user does not have the required roles.
    """
    
    normalized_required_roles = {normalize_role(role) for role in required_roles}
    
    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        @customer_required
        def _impl(*args: P.args, **kwargs: P.kwargs) -> R:
            current_user = g.current_user

            if not current_user:
                return cast(R, error_response("Unauthorized", 401))

            user_roles = cast(list[TUserRole], current_user.roles)
            if not any(normalize_role(user_role.role.name.value) in normalized_required_roles for user_role in user_roles):
                return cast(R, error_response("Access denied: Insufficient permissions", 403))

            return fn(*args, **kwargs)

        return cast(Callable[P, R], _impl)
    return decorator


def admin_required(fn: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator to require admin role (Super Admin, Admin, Operations, CRM Manager, Finance, Support).
    
    Convenience decorator for admin endpoints that require any admin role.
    
    Args:
        fn: The function to decorate.
        
    Returns:
        Decorated function that requires admin role.
    """
    return roles_required("Super Admin", "Admin", "Operations", "CRM Manager", "Finance", "Support")(fn)
