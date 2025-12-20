"""
Clerk authentication integration layer.

This module provides functions to validate Clerk JWTs, introspect sessions,
and create Clerk users programmatically.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from flask import current_app
import requests
import re
import time
from clerk_backend_api import Clerk

from ...logging import log_error, log_event
from ...extensions import db
from ...models.user import AppUser, Profile, Address
from ...models.role import Role, UserRole
from ...enums.auth import RoleNames
from config import Config

# Simple in-memory JWK cache to avoid repeated network calls
_jwks_client_cache: Dict[str, Tuple[float, "PyJWKClient"]] = {}
_JWKS_CACHE_TTL_SECONDS = 300


@dataclass
class AuthenticatedUser:
    """Normalized user object from Clerk authentication."""
    clerk_id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


def get_clerk_client() -> Clerk:
    """
    Get or create a Clerk client instance.
    
    Returns:
        Clerk client instance configured with secret key.
    """
    secret_key = current_app.config.get("CLERK_SECRET_KEY")
    if not secret_key:
        raise ValueError("CLERK_SECRET_KEY not configured")
    
    return Clerk(bearer_auth=secret_key)


def _get_jwks_client(jwks_url: str):
    """Return a cached PyJWKClient for the given JWKS URL."""
    now = time.time()
    cached = _jwks_client_cache.get(jwks_url)
    if cached:
        ts, client = cached
        if now - ts < _JWKS_CACHE_TTL_SECONDS:
            return client
    from jwt import PyJWKClient  # local import to avoid hard dependency at import-time

    client = PyJWKClient(jwks_url)
    _jwks_client_cache[jwks_url] = (now, client)
    return client


def validate_clerk_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a Clerk JWT token and return its payload.
    
    Uses JWKS to verify the signature. Skips iat validation to handle clock skew
    between client/server/Clerk. The exp claim is still validated.
    
    Args:
        token: The JWT token string from Authorization header or cookies.
        
    Returns:
        Decoded token payload if valid, None otherwise.
    """
    try:
        import jwt

        # Decode without verification to extract issuer and audience
        unverified = jwt.decode(token, options={"verify_signature": False})
        issuer = unverified.get("iss", "")
        if "clerk" not in issuer.lower():
            return None

        jwks_url = f"{issuer}/.well-known/jwks.json"
        jwks_client = _get_jwks_client(jwks_url)
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        # Decode with signature verification but skip iat validation
        # to avoid ImmatureSignatureError due to clock skew
        # Use larger leeway for exp to handle token refresh timing
        decoded_payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=unverified.get("aud"),
            issuer=issuer,
            options={
                "verify_iat": False,  # Skip iat validation (clock skew issue)
                "verify_exp": True,   # Still check expiration
                "verify_aud": True,
                "verify_iss": True,
            },
            leeway=300,  # 5 minute leeway for exp (allows for token refresh delays)
        )

        user_id = decoded_payload.get("sub")
        if not user_id:
            return None

        email = decoded_payload.get("email") or decoded_payload.get("https://clerk.dev/email")
        first_name = decoded_payload.get("first_name") or decoded_payload.get("https://clerk.dev/first_name")
        last_name = decoded_payload.get("last_name") or decoded_payload.get("https://clerk.dev/last_name")

        return {
            "user_id": user_id,
            "email": email,
            "phone": decoded_payload.get("phone_number") or decoded_payload.get("https://clerk.dev/phone_number"),
            "first_name": first_name,
            "last_name": last_name,
            "metadata": decoded_payload.get("https://clerk.dev/public_metadata", {}) or {},
        }
    except Exception as e:
        # Treat invalid/expired tokens as unauthenticated (don't spam logs for common cases)
        import jwt as jwt_module
        if isinstance(e, (jwt_module.ExpiredSignatureError, jwt_module.InvalidTokenError)):
            # Expected for expired tokens - don't log full traceback
            pass
        else:
            log_error("Failed to decode Clerk token", error=e)
        return None


def get_clerk_user_from_token(token: str) -> Optional[AuthenticatedUser]:
    """
    Extract and normalize user information from a Clerk token.
    
    Args:
        token: The JWT token string.
        
    Returns:
        AuthenticatedUser object if token is valid, None otherwise.
    """
    payload = validate_clerk_token(token)
    if not payload:
        return None
    
    return AuthenticatedUser(
        clerk_id=payload.get("user_id", ""),
        email=payload.get("email"),
        phone=payload.get("phone"),
        first_name=payload.get("first_name"),
        last_name=payload.get("last_name"),
        metadata=payload.get("metadata", {}),
    )


def get_clerk_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """
    Get a Clerk user by email address.
    
    Args:
        email: User's email address.
        
    Returns:
        Dictionary with user data if found, None otherwise.
    """
    try:
        secret_key = current_app.config.get("CLERK_SECRET_KEY")
        if not secret_key:
            return None
        
        # Clerk API: List users and filter by email
        # Note: Clerk API doesn't have direct email search, so we list and filter
        api_url = "https://api.clerk.com/v1/users"
        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json"
        }
        
        # List users (with limit to avoid fetching too many)
        # Clerk API supports email_address query parameter in some versions
        params = {"limit": 500}  # Adjust limit as needed
        api_response = requests.get(api_url, params=params, headers=headers, timeout=5)
        
        if api_response.status_code == 200:
            response_data = api_response.json()
            
            # Clerk API returns either a list or an object with 'data' key
            users = response_data
            if isinstance(response_data, dict) and 'data' in response_data:
                users = response_data['data']
            
            # Find user with matching email
            if isinstance(users, list):
                for user in users:
                    email_addresses = user.get('email_addresses', [])
                    if email_addresses:
                        for addr in email_addresses:
                            if addr.get('email_address', '').lower() == email.lower():
                                return user
        
        return None
    except Exception as e:
        log_error("Failed to get Clerk user by email", error=e)
        return None


def create_clerk_user(
    email: str,
    password: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone: Optional[str] = None,
    username: Optional[str] = None,
    skip_password_checks: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Create a new user in Clerk via REST API.
    
    Args:
        email: User's email address.
        password: Optional password. If None, Clerk will generate a temporary password.
        first_name: Optional first name.
        last_name: Optional last name.
        phone: Optional phone number.
        username: Optional username. If not provided, will be generated from email.
        skip_password_checks: If True, skip password strength checks (for auto-generated passwords).
        
    Returns:
        Dictionary with clerk_id and other user info if successful, None otherwise.
    """
    try:
        secret_key = current_app.config.get("CLERK_SECRET_KEY")
        if not secret_key:
            log_error("CLERK_SECRET_KEY not configured", error=None)
            return None
        
        # Generate username from email if not provided
        if not username:
            # Extract username part from email (before @)
            username = email.split('@')[0]
            # Clean username: remove special chars, keep alphanumeric and underscores
            username = re.sub(r'[^a-zA-Z0-9_]', '', username)
            # Ensure it's not empty
            if not username:
                username = f"user_{email.split('@')[0][:10]}"
        
        # Prepare user creation payload for REST API
        create_payload = {
            "email_address": [email],
            "username": username,
        }
        
        if password:
            create_payload["password"] = password
            if skip_password_checks:
                create_payload["skip_password_checks"] = True
        
        if first_name:
            create_payload["first_name"] = first_name
        if last_name:
            create_payload["last_name"] = last_name
        if phone:
            create_payload["phone_numbers"] = [phone]
        
        # Use REST API directly for reliability
        api_url = "https://api.clerk.com/v1/users"
        headers = {
            "Authorization": f"Bearer {secret_key}",
            "Content-Type": "application/json"
        }
        
        api_response = requests.post(api_url, json=create_payload, headers=headers, timeout=10)
        
        if api_response.status_code in [200, 201]:
            user_data = api_response.json()
            clerk_id = user_data.get('id')
            
            if clerk_id:
                return {
                    "clerk_id": clerk_id,
                    "email": email,
                    "username": username,
                    "first_name": first_name,
                    "last_name": last_name,
                }
        else:
            error_detail = api_response.json() if api_response.text else {}
            log_error(f"Clerk user creation failed: {api_response.status_code}", error=error_detail)
        
        return None
    except Exception as e:
        log_error("Failed to create Clerk user", error=e)
        return None


def get_or_create_app_user_from_clerk(clerk_user: AuthenticatedUser) -> Optional[AppUser]:
    """
    Get or create an AppUser from Clerk authentication data.
    
    This function first tries to find an existing user by clerk_id or email,
    and creates a new one if not found.
    
    Args:
        clerk_user: AuthenticatedUser from Clerk token validation.
        
    Returns:
        AppUser instance if found/created, None otherwise.
    """
    if not clerk_user or not clerk_user.clerk_id:
        return None
    
    # Try to find existing user by clerk_id
    app_user = AppUser.query.filter_by(clerk_id=clerk_user.clerk_id).first()
    if app_user:
        return app_user
    
    # Try to find by email and link clerk_id
    if clerk_user.email:
        app_user = AppUser.query.filter_by(email=clerk_user.email).first()
        if app_user:
            app_user.clerk_id = clerk_user.clerk_id
            db.session.commit()
            return app_user
    
    # Create new user
    try:
        app_user = AppUser(
            clerk_id=clerk_user.clerk_id,
            email=clerk_user.email,
        )
        db.session.add(app_user)
        db.session.flush()  # Get the ID
        
        # Create profile
        profile = Profile(
            app_user_id=app_user.id,
            firstname=clerk_user.first_name or "",
            lastname=clerk_user.last_name or "",
            phone=clerk_user.phone,
        )
        db.session.add(profile)
        
        # Create address placeholder
        address = Address(app_user_id=app_user.id)
        db.session.add(address)
        
        # Assign default CUSTOMER role
        customer_role = Role.query.filter_by(name=RoleNames.CUSTOMER).first()
        if customer_role:
            UserRole.assign_role(app_user, customer_role, commit=False)
        
        db.session.commit()
        return app_user
    except Exception as e:
        db.session.rollback()
        log_error("Failed to create AppUser from Clerk", error=e)
        return None
