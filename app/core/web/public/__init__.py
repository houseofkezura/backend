from __future__ import annotations

from flask import Blueprint


from .home import bp as home_bp

def create_web_public_blueprint():
    """Create and return the web public blueprint."""
    web_public_bp = Blueprint("web_public", __name__, url_prefix="")
    
    web_public_bp.register_blueprint(home_bp)
    
    return web_public_bp