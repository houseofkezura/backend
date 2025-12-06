from flask import Flask, current_app, url_for
from slugify import slugify
from sqlalchemy import inspect

from .extensions import db
from .models.user import AppUser, Profile, Address
from .models.wallet import Wallet
from .models.role import Role, UserRole
from .logging import log_event

from .enums.auth import RoleNames

def seed_admin_user(clear: bool = False) -> None:
    """
    Seed the database with default Admin User.
    Args:
        clear (bool): If True, Clear existing admin before seeding.
    """
    
    if inspect(db.engine).has_table("role"):
        admin_role = Role.query.filter_by(name=RoleNames.ADMIN).first()
        if not admin_role:
            admin_role = Role()
            admin_role.name = RoleNames.ADMIN
            admin_role.slug = slugify(RoleNames.ADMIN.value)
            db.session.add(admin_role)
            db.session.commit()
    
    if inspect(db.engine).has_table("app_user"):
        admin = (
            AppUser.query
            .join(UserRole, AppUser.id == UserRole.app_user_id)
            .join(Role, UserRole.role_id == Role.id)
            .filter(Role.name == RoleNames.ADMIN)
            .first()
        )

        if clear and admin:
            admin.delete()
            db.session.close()
            log_event("Admin deleted successfully")
            return

        if not admin:
            admin_user = AppUser()
            admin_user.username = current_app.config["DEFAULT_ADMIN_USERNAME"]
            admin_user.email = "admin@admin.com"
            admin_user.password = current_app.config["DEFAULT_ADMIN_PASSWORD"]

            db.session.add(admin_user)
            db.session.flush()  # ensure admin_user.id

            admin_user_profile = Profile()
            admin_user_profile.firstname = "admin"
            admin_user_profile.user_id = admin_user.id

            admin_user_address = Address()
            admin_user_address.user_id = admin_user.id

            admin_user_wallet = Wallet()
            admin_user_wallet.user_id = admin_user.id

            db.session.add_all([admin_user_profile, admin_user_address, admin_user_wallet])
            db.session.commit()

            UserRole.assign_role(admin_user, admin_role)
            log_event("Admin user created with default credentials", event_type="seeding")
        else:
            log_event("Admin user already exists", event_type="seeding")


def seed_roles(clear: bool = False) -> None:
    """Seed database with default roles if the "role" table doesn't exist.

    Args:
        clear (bool, optional): If True, clears all existing roles before seeding. (Defaults to False).
    """
    if inspect(db.engine).has_table("role"):
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

def seed_database(app: Flask) -> None:
    with app.app_context():
        seed_roles()
        seed_admin_user()