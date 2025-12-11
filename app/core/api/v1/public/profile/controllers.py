from __future__ import annotations

from flask import Response, request
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.models.user import AppUser, Profile, Address
from app.schemas.profile import UpdateProfileRequest
from app.logging import log_error, log_event


class ProfileController:
    """Controller for user profile endpoints."""

    @staticmethod
    def get_profile() -> Response:
        """
        Get the authenticated user's profile details.
        
        Returns:
            Complete user profile including profile, address, and wallet information
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            # Ensure profile and address exist
            if not current_user.profile:
                # Create default profile if it doesn't exist
                profile = Profile()
                profile.user_id = current_user.id
                db.session.add(profile)
                db.session.flush()
            
            if not current_user.address:
                # Create default address if it doesn't exist
                address = Address()
                address.user_id = current_user.id
                db.session.add(address)
                db.session.flush()
            
            db.session.commit()
            
            profile_data = current_user.to_dict()
            
            # Include loyalty information if available
            from app.models.loyalty import LoyaltyAccount
            loyalty_account = LoyaltyAccount.query.filter_by(user_id=current_user.id).first()
            if loyalty_account:
                profile_data["loyalty"] = loyalty_account.to_dict()
            
            return success_response(
                "Profile retrieved successfully",
                200,
                {"profile": profile_data}
            )
        except Exception as e:
            log_error("Failed to fetch profile", error=e)
            db.session.rollback()
            return error_response("Failed to fetch profile", 500)
    
    @staticmethod
    def update_profile() -> Response:
        """
        Update the authenticated user's profile details.
        
        Allows updating profile fields (firstname, lastname, gender, phone),
        address fields (country, state), and username.
        
        Returns:
            Updated profile data
        """
        try:
            current_user = get_current_user()
            
            if not current_user:
                return error_response("Unauthorized", 401)
            
            payload = UpdateProfileRequest.model_validate(request.get_json())
            
            # Ensure profile exists
            if not current_user.profile:
                profile = Profile()
                profile.user_id = current_user.id
                db.session.add(profile)
                db.session.flush()
            else:
                profile = current_user.profile
            
            # Ensure address exists
            if not current_user.address:
                address = Address()
                address.user_id = current_user.id
                db.session.add(address)
                db.session.flush()
            else:
                address = current_user.address
            
            # Update profile fields
            if payload.firstname is not None:
                profile.firstname = payload.firstname
            if payload.lastname is not None:
                profile.lastname = payload.lastname
            if payload.gender is not None:
                profile.gender = payload.gender
            if payload.phone is not None:
                profile.phone = payload.phone
            
            # Update address fields
            if payload.country is not None:
                address.country = payload.country
            if payload.state is not None:
                address.state = payload.state
            
            # Update username if provided
            if payload.username is not None:
                # Check if username is already taken by another user
                existing_user = AppUser.query.filter(
                    AppUser.username == payload.username,
                    AppUser.id != current_user.id
                ).first()
                
                if existing_user:
                    return error_response("Username already taken", 409)
                
                current_user.username = payload.username
            
            db.session.commit()
            
            log_event("Profile updated", {"user_id": str(current_user.id)})
            
            # Return updated profile
            profile_data = current_user.to_dict()
            
            return success_response(
                "Profile updated successfully",
                200,
                {"profile": profile_data}
            )
        except IntegrityError as e:
            db.session.rollback()
            log_error("Database integrity error updating profile", error=e)
            return error_response("Failed to update profile. Username or email may already be taken.", 409)
        except Exception as e:
            log_error("Failed to update profile", error=e)
            db.session.rollback()
            return error_response("Failed to update profile", 500)

