'''
This module defines the `roles_required` decorator for the Flask application.

Used for handling role-based access control.
The `roles_required` decorator is used to ensure that the current user has all of the specified roles.
If the user does not have the required roles, it returns a 403 error.

@author: Emmanuel Olowu
@link: https://github.com/zeddyemy
'''
from functools import wraps
from typing import Callable, TypeVar, Any, ParamSpec, cast
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import current_app,  request, redirect, flash, url_for, render_template, Response
from flask.typing import ResponseReturnValue
from flask_login import LoginManager, login_required, current_user as session_user

from app.models.user import AppUser
from app.models.role import UserRole as TUserRole
from app.extensions import db
from ..helpers.loggers import console_log
from ..helpers.api_response import error_response
from ..helpers.user import get_current_user
from ..helpers.roles import normalize_role

# Define type variables for better type hinting
P = ParamSpec('P')
R = TypeVar('R')

def roles_required(*required_roles: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator to ensure that the current user has all of the specified roles.

    This decorator will return a 403 error if the current user does not have
    all of the roles specified in `required_roles`.

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
        def _impl(*args: P.args, **kwargs: P.kwargs) -> R:
            current_user_id = get_jwt_identity()
            current_user = get_current_user()

            if not current_user:
                return cast(R, error_response("Unauthorized", 401))

            user_roles = cast(list[TUserRole], current_user.roles)
            if not any(normalize_role(user_role.role.name.value) in normalized_required_roles for user_role in user_roles):
                return cast(R, error_response("Access denied: Insufficient permissions", 403))

            return fn(*args, **kwargs)

        wrapped = jwt_required()(_impl)
        return cast(Callable[P, R], wrapped)
    return decorator
