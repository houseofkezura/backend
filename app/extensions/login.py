from flask import Flask
from flask_login import LoginManager, UserMixin, current_user

login_manager: LoginManager = LoginManager()

def init_flask_login(app: Flask):
    login_manager.init_app(app)
    setattr(login_manager, 'login_view', 'panel.login')
    
    @login_manager.user_loader
    def load_user(user_id):
        return load_app_user(user_id, app)
    

def load_app_user(user_id: str, app: Flask):
    """Return the `AppUser` with roles for the given ID, or `None` if missing."""
    from app.models import AppUser
    from sqlalchemy.orm import joinedload
    from typing import Any, cast

    try:
        session = cast(Any, db.session)
        return session.get(AppUser, int(user_id), options=[joinedload(cast(Any, AppUser).roles)])
    except Exception as e:
        app.logger.error(f"Error loading user {user_id}: {e}")
        return None
