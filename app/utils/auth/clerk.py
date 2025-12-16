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
import re
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
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": phone,
                }
            else:
                log_error(f"Clerk API response missing user ID: {user_data}", error=None)
                return None
        elif api_response.status_code == 422:
            # User might already exist, try to get existing user
            error_data = api_response.json()
            errors = error_data.get('errors', [])
            
            # Check if error is about existing identifier
            identifier_exists = any(
                err.get('code') == 'form_identifier_exists' 
                for err in errors
            )
            
            if identifier_exists:
                # Try to get existing user by email
                existing_user = get_clerk_user_by_email(email)
                if existing_user and existing_user.get('id'):
                    log_event(f"User already exists in Clerk, using existing user: {existing_user.get('id')}")
                    return {
                        "clerk_id": existing_user.get('id'),
                        "email": email,
                        "first_name": existing_user.get('first_name') or first_name,
                        "last_name": existing_user.get('last_name') or last_name,
                        "phone": phone,
                    }
            
            error_detail = api_response.text
            log_error(
                f"Clerk API returned status {api_response.status_code}: {error_detail}",
                error=None
            )
            return None
        else:
            error_detail = api_response.text
            log_error(
                f"Clerk API returned status {api_response.status_code}: {error_detail}",
                error=None
            )
            return None
            
    except Exception as e:
        log_error("Failed to create Clerk user", error=e)
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

