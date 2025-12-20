'''
This module defines authentication and authorization decorators for the Flask application.

Used for handling Clerk-based authentication and role-based access control.
The decorators validate Clerk tokens and enforce RBAC using roles stored in the database.

@author: Emmanuel Olowu
@link: https://github.com/zeddyemy
'''
from functools import wraps
from typing import Callable, TypeVar, Any, ParamSpec, cast, Optional, Iterable, Set
from flask import g, request, Response, redirect, url_for, abort
from flask.typing import ResponseReturnValue

from app.models.user import AppUser
from app.models.role import UserRole as TUserRole
from app.extensions import db
from quas_utils.logging.loggers import console_log
from quas_utils.api import error_response
from ..helpers.roles import normalize_role
from ..auth.clerk import get_clerk_user_from_token, get_or_create_app_user_from_clerk

# Allowed roles for admin UI (any of these can enter)
ADMIN_ALLOWED_ROLES = {
    "super admin",
    "admin",
    "operations",
    "crm manager",
    "crm staff",
    "finance",
    "support",
}

# Define type variables for better type hinting
P = ParamSpec('P')
R = TypeVar('R')


def _get_auth_token_from_request() -> Optional[str]:
    """
    Extract Clerk token from Authorization header or Clerk session cookies.
    Cookie names follow Clerk defaults: __session (hosted) or clerk_session.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]

    # Fallback to common Clerk cookies
    cookie_token = (
        request.cookies.get("__session")
        or request.cookies.get("clerk_session")
        or request.cookies.get("__clerk")
    )
    return cookie_token


def _load_existing_app_user(clerk_user) -> Optional[AppUser]:
    """
    Load an existing AppUser using clerk_id or email.
    This avoids creating new users for the admin UI path.
    """
    if not clerk_user:
        return None

    # First: by clerk_id
    if clerk_user.clerk_id:
        app_user = AppUser.query.filter_by(clerk_id=clerk_user.clerk_id).first()
        if app_user:
            return app_user

    # Fallback: by email, then link clerk_id for future lookups
    if clerk_user.email:
        app_user = AppUser.query.filter_by(email=clerk_user.email).first()
        if app_user:
            if not app_user.clerk_id:
                app_user.clerk_id = clerk_user.clerk_id
                db.session.commit()
            return app_user

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
        token = _get_auth_token_from_request()
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


def optional_customer_auth(fn: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator for endpoints that support both authenticated and guest access.
    
    If a Clerk token is present, validates it and sets g.current_user.
    If no token is present, allows the request to proceed (for guest access).
    
    Use this for endpoints like orders that support both authenticated users
    and guest users (via email query param).
    
    Args:
        fn: The function to decorate.
        
    Returns:
        Decorated function that optionally validates authentication.
    """
    @wraps(fn)
    def _impl(*args: P.args, **kwargs: P.kwargs) -> R:
        token = _get_auth_token_from_request()
        
        # If token is present, validate it and set g.current_user
        if token:
            clerk_user = get_clerk_user_from_token(token)
            if clerk_user:
                app_user = get_or_create_app_user_from_clerk(clerk_user)
                if app_user:
                    g.current_user = app_user
            # If token is invalid, we don't fail - allow guest access
            # The controller will handle authorization checks
        
        return fn(*args, **kwargs)
    
    return cast(Callable[P, R], _impl)


def _user_has_any_role(user: AppUser, allowed_roles: Set[str]) -> bool:
    user_roles = cast(list[TUserRole], user.roles)
    return any(
        normalize_role(user_role.role.name.value) in allowed_roles
        for user_role in user_roles
    )


def roles_required_web(
    *required_roles: str,
    login_endpoint: str = "web.web_admin.web_admin_auth.login",
    redirect_to_login: bool = True,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator for web routes that enforces Clerk auth + specific roles.
    - Uses cookies or Authorization header for Clerk token.
    - Does not auto-create AppUser; requires existing user with allowed roles.
    - NEVER uses abort() - always returns redirects to prevent error handler interference.
    """
    normalized_required_roles = {normalize_role(role) for role in required_roles}

    def decorator(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def _impl(*args: P.args, **kwargs: P.kwargs) -> R:
            def _redirect_with_cookie_clear() -> R:
                """Helper to redirect to login and clear cookies."""
                resp = redirect(url_for(login_endpoint, next=request.url, _external=False))
                # Clear common Clerk cookies to avoid redirect loops on expired tokens
                for cookie_name in ("__session", "clerk_session", "__clerk"):
                    resp.delete_cookie(cookie_name, path="/")
                return cast(R, resp)

            token = _get_auth_token_from_request()
            if not token:
                if redirect_to_login:
                    return _redirect_with_cookie_clear()
                # For web routes, always redirect instead of abort
                return _redirect_with_cookie_clear()

            clerk_user = get_clerk_user_from_token(token)
            if not clerk_user:
                if redirect_to_login:
                    return _redirect_with_cookie_clear()
                # For web routes, always redirect instead of abort
                return _redirect_with_cookie_clear()

            app_user = _load_existing_app_user(clerk_user)
            if not app_user:
                # User doesn't exist in our DB - redirect to login
                return _redirect_with_cookie_clear()

            if normalized_required_roles and not _user_has_any_role(
                app_user, normalized_required_roles
            ):
                # User doesn't have required role - redirect to login
                return _redirect_with_cookie_clear()

            g.current_user = app_user
            return fn(*args, **kwargs)

        return cast(Callable[P, R], _impl)

    return decorator


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
            if not any(
                normalize_role(user_role.role.name.value) in normalized_required_roles
                for user_role in user_roles
            ):
                return cast(
                    R, error_response("Access denied: Insufficient permissions", 403)
                )

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
