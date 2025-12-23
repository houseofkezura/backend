from flask import Flask, current_app, url_for
from slugify import slugify
from sqlalchemy import inspect

from .extensions import db
from .models.user import AppUser, Profile, Address
from .models.wallet import Wallet
from .models.role import Role, UserRole
from .models.category import ProductCategory
from .logging import log_event, log_error

from .enums.auth import RoleNames
from .utils.auth.clerk import create_clerk_user, get_clerk_user_by_email

def seed_admin_user(clear: bool = False) -> None:
    """
    Seed the database with default Super Admin User using Clerk.
    Args:
        clear (bool): If True, Clear existing admin before seeding.
    """
    
    if not inspect(db.engine).has_table("role"):
        log_event("Role table does not exist, skipping admin user seeding", event_type="seeding")
        return
    
    # Get or create Super Admin role
    super_admin_role = Role.query.filter_by(name=RoleNames.SUPER_ADMIN).first()
    if not super_admin_role:
        super_admin_role = Role()
        super_admin_role.name = RoleNames.SUPER_ADMIN
        super_admin_role.slug = slugify(RoleNames.SUPER_ADMIN.value)
        db.session.add(super_admin_role)
        db.session.commit()
    
    if not inspect(db.engine).has_table("app_user"):
        log_event("AppUser table does not exist, skipping admin user seeding", event_type="seeding")
        return
    
    # Check if super admin already exists
    existing_super_admin = (
        AppUser.query
        .join(UserRole, AppUser.id == UserRole.app_user_id)
        .join(Role, UserRole.role_id == Role.id)
        .filter(Role.name == RoleNames.SUPER_ADMIN)
        .first()
    )

    if clear and existing_super_admin:
        # Note: This only deletes from our DB, not from Clerk
        # You may want to handle Clerk deletion separately if needed
        db.session.delete(existing_super_admin)
        db.session.commit()
        log_event("Super Admin deleted successfully", event_type="seeding")
        return

    if existing_super_admin:
        log_event("Super Admin user already exists", event_type="seeding")
        return
    
    # Get super admin credentials from config
    super_admin_email = current_app.config.get("SUPER_ADMIN_EMAIL") or "admin@kezura.com"
    super_admin_password = current_app.config.get("SUPER_ADMIN_PASSWORD") or "ChangeMe123!"
    super_admin_firstname = current_app.config.get("SUPER_ADMIN_FIRSTNAME") or "Super"
    super_admin_lastname = current_app.config.get("SUPER_ADMIN_LASTNAME") or "Admin"
    super_admin_username = current_app.config.get("SUPER_ADMIN_USERNAME") or "superadmin"
    
    try:
        # Check if user already exists in Clerk
        existing_clerk_user = get_clerk_user_by_email(super_admin_email)
        
        if existing_clerk_user:
            # User exists in Clerk, use existing user
            clerk_id = existing_clerk_user.get('id')
            log_event(
                f"Found existing Clerk user for super admin. Email: {super_admin_email}, Clerk ID: {clerk_id}",
                event_type="seeding"
            )
        else:
            # Create user in Clerk
            clerk_user_data = create_clerk_user(
                email=super_admin_email,
                password=super_admin_password,
                first_name=super_admin_firstname,
                last_name=super_admin_lastname,
                username=super_admin_username,
                skip_password_checks=False
            )
            
            if not clerk_user_data or not clerk_user_data.get("clerk_id"):
                log_error("Failed to create Clerk user for super admin", error=None)
                return
            
            clerk_id = clerk_user_data["clerk_id"]
        
        # Create AppUser in database
        admin_user = AppUser()
        admin_user.clerk_id = clerk_id
        admin_user.email = super_admin_email
        admin_user.username = super_admin_username
        
        db.session.add(admin_user)
        db.session.flush()  # Ensure admin_user.id is available
        
        # Create Profile
        admin_user_profile = Profile()
        admin_user_profile.firstname = super_admin_firstname
        admin_user_profile.lastname = super_admin_lastname
        admin_user_profile.user_id = admin_user.id
        db.session.add(admin_user_profile)
        
        # Create Address
        admin_user_address = Address()
        admin_user_address.user_id = admin_user.id
        db.session.add(admin_user_address)
        
        # Create Wallet
        admin_user_wallet = Wallet()
        admin_user_wallet.user_id = admin_user.id
        db.session.add(admin_user_wallet)
        
        db.session.commit()
        
        # Assign Super Admin role
        UserRole.assign_role(admin_user, super_admin_role, commit=True)
        
        log_event(
            f"Super Admin user created successfully. Email: {super_admin_email}, Clerk ID: {clerk_id}",
            event_type="seeding"
        )
        
    except Exception as e:
        log_error("Failed to create Super Admin user", error=e)
        db.session.rollback()
        raise


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


def seed_product_categories(clear: bool = False) -> None:
    prod_cat = [
        {
        "name" : "Wigs / Hair",
        "alias" : "HW"
        },
        {
        "name" : "Jewelry",
        "alias" : "JW"
        },
        {
        "name" : "Perfume",
        "alias" : "PF"
        },
        {
        "name": "Skincare",
        "alias" : "SC"
        },
        {
        "name" : "Supplements",
        "alias" : "SP"
        },
        {
        "name" : "Misc",
        "alias" : "MC"
        }
    ]
    if inspect(db.engine).has_table("product_category"):
        if clear:
            ProductCategory.query.delete()
            db.session.commit()
        
        for cat in prod_cat:
            if not ProductCategory.query.filter_by(name=cat["name"]).first():
                new_category = ProductCategory()
                new_category.name = cat["name"]
                new_category.alias = cat["alias"]
                new_category.slug = slugify(cat["name"])
                db.session.add(new_category)
        db.session.commit()

def seed_database(app: Flask) -> None:
    with app.app_context():
        seed_roles()
        seed_admin_user()
        seed_product_categories()