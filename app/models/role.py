from __future__ import annotations
from typing import TYPE_CHECKING

from enum import Enum
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Query, Mapped as M  # type: ignore
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..extensions import db
from .user import AppUser
from ..enums.auth import RoleNames
from quas_utils.date_time import QuasDateTime
from ..logging import log_event


if TYPE_CHECKING:
    from .role import Role as TRole
    from .role import UserRole as TUserRole

# Role data model
class Role(db.Model):
    """ Role data model """
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = db.Column(db.Enum(RoleNames), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(100), nullable=True)
    
    # Relationship to UserRole
    role_assignments = db.relationship(
        'UserRole',
        back_populates='role',
        cascade="all, delete-orphan"
    )
    
    def __str__(self) -> str:
        return self.name.value.capitalize()
    
    def update(self, commit=True, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if commit:
            db.session.commit()

    def delete(self, commit=True):
        db.session.delete(self)
        if commit:
            db.session.commit()

class UserRole(db.Model):
    """Association object for AppUser and Role with additional metadata."""
    __tablename__ = 'user_role'

    app_user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('app_user.id'), primary_key=True)
    role_id = db.Column(UUID(as_uuid=True), db.ForeignKey('role.id'), primary_key=True)
    assigner_id = db.Column(UUID(as_uuid=True), db.ForeignKey('app_user.id'), nullable=True)
    assigned_at = db.Column(db.DateTime(timezone=True), default=QuasDateTime.aware_utcnow, nullable=False)

    # Relationships to track who assigned the role
    user= db.relationship('AppUser', back_populates='roles', foreign_keys=[app_user_id])
    assigner= db.relationship('AppUser', back_populates='assigned_roles', foreign_keys=[assigner_id])
    role= db.relationship('Role', back_populates='role_assignments')
    
    @classmethod
    def assign_role(cls, user, role, assigner=None, commit=True):
        """
        Assigns a role to a user, tracking who assigned it.
        
        :param user: AppUser instance to assign the role to.
        :param role: Role instance to assign.
        :param assigner: AppUser instance who is assigning the role.
        :return: UserRole instance.
        :raises: ValueError if role or users are invalid, IntegrityError for duplicate assignments.
        """
        
        if not isinstance(user, AppUser):
            raise ValueError("user must be an instance of AppUser.")
        
        if not isinstance(role, Role):
            raise ValueError("role must be an instance of Role.")
        
        if assigner and not isinstance(assigner, AppUser):
            raise ValueError("assigner must be an instance of AppUser.")
        
        # Check if the user already has the role
        existing_user_role = cls.query.filter_by(app_user_id=user.id, role_id=role.id).first()
        if not existing_user_role:
            user_role = cls()
            user_role.app_user_id = user.id
            user_role.role_id = role.id

            if assigner:
                user_role.assigner_id = assigner.id

            db.session.add(user_role)

            if commit:
                try:
                    db.session.commit()
                except IntegrityError as e:
                    db.session.rollback()
                    # Avoid strict type complaint: e.orig can be Optional
                    raise IntegrityError(
                        "Failed to assign role due to integrity constraints.",
                        e.params,
                        e.orig or Exception("Integrity error"),
                    )

            assigner_name = assigner.username if assigner else "default"
            log_event(data=f"Role '{role.name.value}' assigned to user '{user.username}' by '{assigner_name}'.")

            return user_role
        
        return existing_user_role
    
    
    @classmethod
    def revoke_role(cls, user_to_revoke, role, revoker):
        """
        Revokes a role from a user, tracking who revoked it.

        :param user_to_revoke: AppUser instance to revoke the role from.
        :param role: Role instance to revoke.
        :param revoker: AppUser instance who is revoking the role.
        :return: None
        :raises: ValueError if inputs are invalid or role not assigned.
        """
        if not isinstance(user_to_revoke, AppUser):
            raise ValueError("user_to_revoke must be an instance of AppUser.")
        
        if not isinstance(role, Role):
            raise ValueError("role must be an instance of Role.")
        
        if not isinstance(revoker, AppUser):
            raise ValueError("revoker must be an instance of AppUser.")
        
        # Find the existing UserRole entry
        user_role = cls.query.filter_by(app_user_id=user_to_revoke.id, role_id=role.id).first()
        if not user_role:
            raise ValueError("Role not assigned to the user.")
        
        # TODO: Optionally, log who revoked the role and when
        
        # delete (revoke) user role
        db.session.delete(user_role)
        db.session.commit()

    def update(self, commit=True, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        if commit:
            db.session.commit()

    def delete(self, commit=True):
        db.session.delete(self)
        if commit:
            db.session.commit()


