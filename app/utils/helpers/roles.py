"""
Author: Emmanuel Olowu
Link: https://github.com/zeddyemy
Copyright: © 2024 Emmanuel Olowu <zeddyemy@gmail.com>
License: GNU, see LICENSE for more details.
Package: Kezura
"""

from slugify import slugify
from sqlalchemy import desc, inspect
from sqlalchemy.exc import DataError, DatabaseError
from werkzeug.security import generate_password_hash

from ...extensions import db
from ...enums.auth import RoleNames
from ...models.role import Role
from ...models.user import AppUser, Profile, Address
from quas_utils.logging.loggers import console_log, log_exception

def get_role_names(as_enum=False):
    """returns a list containing the names of all the roles"""
    role_names = []
    
    all_roles = db.session.query(Role.name).order_by(desc('id')).all()
    console_log('all_roles', all_roles)
    
    for role in all_roles:
        if as_enum:
            role_names.append(role.name)
        else:
            role_names.append(role.name.value)
    
    
    return role_names

def get_role_id(role_name):
    """Return the role id for a given role name (string or RoleNames)."""
    # Normalize input to RoleNames enum if a string is provided
    role_enum = role_name if isinstance(role_name, RoleNames) else RoleNames.get_member_by_value(role_name)
    customer_enum = RoleNames.CUSTOMER

    role_from_db = Role.query.filter_by(name=role_enum).first() if role_enum else None
    customer_role = Role.query.filter_by(name=customer_enum).first()

    if role_from_db and hasattr(role_from_db, 'id'):
        return role_from_db.id
    if customer_role and hasattr(customer_role, 'id'):
        return customer_role.id
    raise ValueError("No matching role found and default customer role is missing")

def admin_roles():
    all_roles = Role.query.filter(Role.name != 'Customer').all()
    admin_roles = [role.name.value for role in all_roles]
    
    return admin_roles

def admin_editor_roles():
    all_roles = Role.query.filter(Role.name.in_(['Administrator', 'Editor'])).all()
    admin_editor_roles = [role.name for role in all_roles]
    
    return admin_editor_roles


def create_super_admin():
    try:
        super_admin_role = Role.query.filter_by(name=RoleNames.ADMIN).first()
        
        if not super_admin_role:
            raise ValueError("No role found with the name ADMIN")
        
        super_admins = super_admin_role.users.first()
        
        if not super_admins:
            super_admin = AppUser()
            super_admin.username = 'admin'
            super_admin.email = 'admin@mail.com'
            super_admin.password_hash = generate_password_hash('root', "pbkdf2:sha256")

            db.session.add(super_admin)
            db.session.flush()  # ensure super_admin.id is available

            super_admin_profile = Profile()
            super_admin_profile.firstname = 'Admin'
            super_admin_profile.user_id = super_admin.id

            super_admin_address = Address()
            super_admin_address.user_id = super_admin.id
        
            # Assign role via association table or a helper (append may be via a secondary relationship in another model)
            # Fall back to direct association object creation if needed
            try:
                super_admin.roles.append(super_admin_role)  # type: ignore[attr-defined]
            except Exception:
                from ...models.role import UserRole  # local import to avoid cycles
                user_role = UserRole()
                user_role.app_user_id = super_admin.id
                user_role.role_id = super_admin_role.id
                db.session.add(user_role)
            
            db.session.add_all([super_admin, super_admin_profile, super_admin_address])
            db.session.commit()
    except (DataError, DatabaseError) as e:
        db.session.rollback()
        log_exception('Database error occurred during registration', e)
        raise e
    except Exception as e:
        db.session.rollback()
        log_exception('Error creating Admin User', e)
        raise e
    
def create_roles_and_super_admin(clear: bool = False) -> None:
    """Creates default roles if the 'role' table doesn't exist.

    Args:
        clear (bool, optional): If True, clears all existing roles before creating new ones. Defaults to False.
    """
    if inspect(db.engine).has_table('role'):
        if clear:
            # Clear existing roles before creating new ones
            Role.query.delete()
            db.session.commit()
        
        for role_name in RoleNames:
            if not Role.query.filter_by(name=role_name).first():
                new_role = Role()
                new_role.name = role_name
                new_role.slug = slugify(role_name.value)
                db.session.add(new_role)
        db.session.commit()
        
        create_super_admin()


def normalize_role(role: str) -> str:
    """
    Normalize role name by converting to lowercase and removing extra spaces.
    
    Args:
        role (str): Role name to normalize
        
    Returns:
        str: Normalized role name
        
    Example:
        >>> normalize_role("Admin ")
        "admin"
        >>> normalize_role("SUPER ADMIN")
        "super admin"
    """
    return role.strip().lower()

