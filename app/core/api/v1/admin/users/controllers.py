"""
Admin user controller.
"""

from __future__ import annotations

from flask import Response, request
import uuid

from app.extensions import db
from app.models.user import AppUser, Profile
from sqlalchemy import or_
from app.models.role import Role, UserRole
from app.models.audit import AuditLog
from app.enums.auth import RoleNames
from quas_utils.api import success_response, error_response
from app.utils.helpers.user import get_current_user
from app.logging import log_error, log_event


class AdminUserController:
    """Controller for admin user endpoints."""

    @staticmethod
    def list_users() -> Response:
        """
        List all users with optional filtering and pagination.
        
        Requires admin authentication.
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            # Get query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 20, type=int)
            search = request.args.get('search', type=str)
            role = request.args.get('role', type=str)
            
            # Build query
            query = AppUser.query
            
            if search:
                from sqlalchemy.orm import outerjoin
                query = query.outerjoin(Profile).filter(
                    or_(
                        AppUser.email.ilike(f'%{search}%'),
                        AppUser.username.ilike(f'%{search}%'),
                        Profile.firstname.ilike(f'%{search}%'),
                        Profile.lastname.ilike(f'%{search}%')
                    )
                )
            
            if role:
                # Filter by role
                role_obj = Role.query.filter_by(name=RoleNames.get_member_by_value(role)).first()
                if role_obj:
                    query = query.join(UserRole).filter(UserRole.role_id == role_obj.id)
            
            # Order by date_joined desc
            query = query.order_by(AppUser.date_joined.desc())
            
            # Paginate
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            
            users = [u.to_dict() for u in pagination.items]
            
            return success_response(
                "Users retrieved successfully",
                200,
                {
                    "users": users,
                    "pagination": {
                        "page": page,
                        "per_page": per_page,
                        "total": pagination.total,
                        "pages": pagination.pages
                    }
                }
            )
        except Exception as e:
            log_error("Failed to list users", error=e)
            return error_response("Failed to retrieve users", 500)

    @staticmethod
    def get_user(user_id: str) -> Response:
        """
        Get a single user by ID.
        
        Args:
            user_id: User ID
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                return error_response("Invalid user ID format", 400)
            
            user = AppUser.query.get(user_uuid)
            if not user:
                return error_response("User not found", 404)
            
            user_data = user.to_dict()
            
            # Include additional admin info
            from app.models.loyalty import LoyaltyAccount
            loyalty_account = db.session.query(LoyaltyAccount).filter_by(user_id=user.id).first()
            if loyalty_account:
                user_data["loyalty"] = loyalty_account.to_dict()
            
            return success_response(
                "User retrieved successfully",
                200,
                {"user": user_data}
            )
        except Exception as e:
            log_error(f"Failed to get user {user_id}", error=e)
            return error_response("Failed to retrieve user", 500)

    @staticmethod
    def assign_role(user_id: str) -> Response:
        """
        Assign a role to a user.
        
        Args:
            user_id: User ID
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                return error_response("Invalid user ID format", 400)
            
            user = AppUser.query.get(user_uuid)
            if not user:
                return error_response("User not found", 404)
            
            from app.schemas.admin import AssignRoleRequest
            payload = AssignRoleRequest.model_validate(request.get_json() or {})
            role_name = payload.role
            
            if not role_name:
                return error_response("Role is required", 400)
            
            # Get role
            role_enum = RoleNames.get_member_by_value(role_name)
            if not role_enum:
                return error_response("Invalid role", 400)
            
            role = Role.query.filter_by(name=role_enum).first()
            if not role:
                return error_response("Role not found", 404)
            
            # Check if user already has this role
            existing = UserRole.query.filter_by(app_user_id=user.id, role_id=role.id).first()
            if existing:
                return error_response("User already has this role", 409)
            
            # Assign role
            UserRole.assign_role(user, role, commit=True)
            
            # Create audit log
            AuditLog.log_action(
                action="role_assigned",
                user_id=current_user.id,
                resource_type="user",
                resource_id=user_uuid,
                meta={
                    "assigned_role": role_name,
                    "target_user_id": str(user.id),
                }
            )
            
            log_event(f"Role {role_name} assigned to user {user_id} by admin {current_user.id}")
            
            return success_response(
                "Role assigned successfully",
                200,
                {"user": user.to_dict()}
            )
        except Exception as e:
            log_error(f"Failed to assign role to user {user_id}", error=e)
            db.session.rollback()
            return error_response("Failed to assign role", 500)

    @staticmethod
    def revoke_role(user_id: str) -> Response:
        """
        Revoke a role from a user.
        
        Args:
            user_id: User ID
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                return error_response("Invalid user ID format", 400)
            
            user = AppUser.query.get(user_uuid)
            if not user:
                return error_response("User not found", 404)
            
            from app.schemas.admin import AssignRoleRequest
            payload = AssignRoleRequest.model_validate(request.get_json() or {})
            role_name = payload.role
            
            if not role_name:
                return error_response("Role is required", 400)
            
            # Get role
            role_enum = RoleNames.get_member_by_value(role_name)
            if not role_enum:
                return error_response("Invalid role", 400)
            
            role = Role.query.filter_by(name=role_enum).first()
            if not role:
                return error_response("Role not found", 404)
            
            # Find and remove role
            user_role = UserRole.query.filter_by(app_user_id=user.id, role_id=role.id).first()
            if not user_role:
                return error_response("User does not have this role", 404)
            
            db.session.delete(user_role)
            db.session.commit()
            
            # Create audit log
            AuditLog.log_action(
                action="role_revoked",
                user_id=current_user.id,
                resource_type="user",
                resource_id=user_uuid,
                meta={
                    "revoked_role": role_name,
                    "target_user_id": str(user.id),
                }
            )
            
            log_event(f"Role {role_name} revoked from user {user_id} by admin {current_user.id}")
            
            return success_response(
                "Role revoked successfully",
                200,
                {"user": user.to_dict()}
            )
        except Exception as e:
            log_error(f"Failed to revoke role from user {user_id}", error=e)
            db.session.rollback()
            return error_response("Failed to revoke role", 500)

    @staticmethod
    def deactivate_user(user_id: str) -> Response:
        """
        Deactivate a user account.
        
        Args:
            user_id: User ID
        """
        try:
            current_user = get_current_user()
            if not current_user:
                return error_response("Unauthorized", 401)
            
            try:
                user_uuid = uuid.UUID(user_id)
            except ValueError:
                return error_response("Invalid user ID format", 400)
            
            user = AppUser.query.get(user_uuid)
            if not user:
                return error_response("User not found", 404)
            
            # For now, we'll add an is_active flag or use a role-based approach
            # Since we don't have is_active, we'll remove all roles except CUSTOMER
            # This effectively deactivates admin access
            customer_role = Role.query.filter_by(name=RoleNames.CUSTOMER).first()
            if customer_role:
                # Remove all non-customer roles
                UserRole.query.filter(
                    UserRole.app_user_id == user.id,
                    UserRole.role_id != customer_role.id
                ).delete()
                db.session.commit()
            
            # Create audit log
            AuditLog.log_action(
                action="user_deactivated",
                user_id=current_user.id,
                resource_type="user",
                resource_id=user_uuid,
                meta={
                    "target_user_id": str(user.id),
                }
            )
            
            log_event(f"User {user_id} deactivated by admin {current_user.id}")
            
            return success_response(
                "User deactivated successfully",
                200,
                {"user": user.to_dict()}
            )
        except Exception as e:
            log_error(f"Failed to deactivate user {user_id}", error=e)
            db.session.rollback()
            return error_response("Failed to deactivate user", 500)

