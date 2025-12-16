"""
Clerk authentication integration layer.

This module provides functions to validate Clerk JWTs, introspect sessions,
and create Clerk users programmatically.
"""

from __future__ import annotations

from typing import Optional, Dict, Any
from dataclasses import dataclass
from flask import current_app
import requests
from clerk_backend_api import Clerk

from ...logging import log_error, log_event
from ...extensions import db
from ...models.user import AppUser, Profile, Address
from ...models.role import Role, UserRole
from ...enums.auth import RoleNames
from config import Config


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


def validate_clerk_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a Clerk JWT token and return its payload.
    
    This function validates both session tokens and JWT tokens from Clerk.
    For JWT tokens, it decodes and verifies using Clerk's public keys.
    For session tokens, it uses Clerk's verify_token API.
    
    Args:
        token: The JWT or session token string from Authorization header.
        
    Returns:
        Decoded token payload if valid, None otherwise.
    """
    try:
        client = get_clerk_client()
        user_id = None
        decoded_payload = None
        
        # Try to verify as a session token first
        try:
            response = client.sessions.verify_token(token=token)
            if response and hasattr(response, 'user_id'):
                user_id = response.user_id
            else:
                return None
        except Exception:
            # If verify_token fails, try to decode as JWT
            try:
                import jwt
                from jwt import PyJWKClient
                
                # Decode without verification first to get the issuer
                unverified = jwt.decode(token, options={"verify_signature": False})
                issuer = unverified.get("iss", "")
                
                # Get Clerk's JWKS URL from issuer
                if "clerk" in issuer.lower():
                    jwks_url = f"{issuer}/.well-known/jwks.json"
                    jwks_client = PyJWKClient(jwks_url)
                    signing_key = jwks_client.get_signing_key_from_jwt(token)
                    
                    # Verify and decode the token
                    decoded_payload = jwt.decode(
                        token,
                        signing_key.key,
                        algorithms=["RS256"],
                        audience=unverified.get("aud"),
                        issuer=issuer,
                    )
                    
                    user_id = decoded_payload.get("sub")
                    if not user_id:
                        return None
                else:
                    return None
            except Exception as jwt_error:
                log_error("Failed to decode JWT token", error=jwt_error)
                return None
        
        if not user_id:
            return None
        
        # Try to extract user info from JWT payload first (more efficient)
        if decoded_payload:
            # JWT tokens often contain email and other claims
            email = decoded_payload.get("email") or decoded_payload.get("https://clerk.dev/email")
            first_name = decoded_payload.get("first_name") or decoded_payload.get("https://clerk.dev/first_name")
            last_name = decoded_payload.get("last_name") or decoded_payload.get("https://clerk.dev/last_name")
            
            # If we have email from JWT, use it (avoid API call)
            if email:
                return {
                    "user_id": user_id,
                    "email": email,
                    "phone": decoded_payload.get("phone_number") or decoded_payload.get("https://clerk.dev/phone_number"),
                    "first_name": first_name,
                    "last_name": last_name,
                    "metadata": decoded_payload.get("https://clerk.dev/public_metadata", {}) or {},
                }
        
        # Fallback: Fetch user details from Clerk API if not in JWT
        # Use REST API directly for reliability
        try:
            secret_key = current_app.config.get("CLERK_SECRET_KEY")
            api_url = f"https://api.clerk.com/v1/users/{user_id}"
            headers = {
                "Authorization": f"Bearer {secret_key}",
                "Content-Type": "application/json"
            }
            
            api_response = requests.get(api_url, headers=headers, timeout=5)
            if api_response.status_code == 200:
                user_data = api_response.json()
                email_addresses = user_data.get('email_addresses', [])
                phone_numbers = user_data.get('phone_numbers', [])
                
                return {
                    "user_id": user_id,
                    "email": email_addresses[0].get('email_address') if email_addresses else None,
                    "phone": phone_numbers[0].get('phone_number') if phone_numbers else None,
                    "first_name": user_data.get('first_name'),
                    "last_name": user_data.get('last_name'),
                    "metadata": user_data.get('public_metadata', {}) or {},
                }
            else:
                log_error(f"Clerk API returned status {api_response.status_code}", error=None)
        except Exception as api_error:
            log_error("Failed to fetch user from Clerk API", error=api_error)
        
        # Return minimal info if we have user_id but couldn't fetch details
        # This allows authentication to proceed even if user details fetch fails
        return {
            "user_id": user_id,
            "email": None,
            "phone": None,
            "first_name": None,
            "last_name": None,
            "metadata": {},
        }
    except Exception as e:
        log_error("Failed to validate Clerk token", error=e)
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


def create_clerk_user(
    email: str,
    password: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone: Optional[str] = None,
    skip_password_checks: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Create a new user in Clerk via API.
    
    Args:
        email: User's email address.
        password: Optional password. If None, Clerk will generate a temporary password.
        first_name: Optional first name.
        last_name: Optional last name.
        phone: Optional phone number.
        skip_password_checks: If True, skip password strength checks (for auto-generated passwords).
        
    Returns:
        Dictionary with clerk_id and other user info if successful, None otherwise.
    """
    try:
        client = get_clerk_client()
        
        # Prepare user creation payload
        create_payload = {
            "email_address": [email],
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
        
        # Create user in Clerk
        user = client.users.create_user(**create_payload)
        
        if user and hasattr(user, 'id'):
            return {
                "clerk_id": user.id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "phone": phone,
            }
    except Exception as e:
        log_error("Failed to create Clerk user", error=e)
        return None
    
    return None


def get_or_create_app_user_from_clerk(clerk_user: AuthenticatedUser) -> Optional[AppUser]:
    """
    Get existing AppUser by clerk_id, or create a new one if it doesn't exist.
    
    This function handles the mapping between Clerk users and our internal AppUser model.
    It also creates related Profile, Address, and Wallet records if needed.
    
    Args:
        clerk_user: AuthenticatedUser object from Clerk.
        
    Returns:
        AppUser instance if successful, None otherwise.
    """
    try:
        # Try to find existing user by clerk_id
        app_user = AppUser.query.filter_by(clerk_id=clerk_user.clerk_id).first()
        
        if app_user:
            # Update email if it changed in Clerk
            if clerk_user.email and app_user.email != clerk_user.email:
                app_user.email = clerk_user.email
                db.session.commit()
            return app_user
        
        # Try to find by email (in case clerk_id wasn't set but email matches)
        if clerk_user.email:
            app_user = AppUser.query.filter_by(email=clerk_user.email).first()
            if app_user:
                # Link existing user to Clerk
                app_user.clerk_id = clerk_user.clerk_id
                db.session.commit()
                return app_user
        
        # Create new AppUser
        app_user = AppUser()
        app_user.clerk_id = clerk_user.clerk_id
        app_user.email = clerk_user.email
        
        db.session.add(app_user)
        db.session.flush()
        
        # Create Profile
        profile = Profile()
        profile.firstname = clerk_user.first_name or ""
        profile.lastname = clerk_user.last_name or ""
        profile.user_id = app_user.id
        db.session.add(profile)
        
        # Create Address
        address = Address()
        address.user_id = app_user.id
        db.session.add(address)
        
        # Assign default CUSTOMER role
        role = Role.query.filter_by(name=RoleNames.CUSTOMER).first()
        if role:
            UserRole.assign_role(app_user, role, commit=False)
        
        db.session.commit()
        
        log_event(f"Created new AppUser from Clerk: {clerk_user.clerk_id}")
        return app_user
        
    except Exception as e:
        log_error("Failed to get or create AppUser from Clerk", error=e)
        db.session.rollback()
        return None

