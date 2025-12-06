"""
Author: Emmanuel Olowu
Link: https://github.com/zeddyemy
Copyright: © 2024 Emmanuel Olowu <zeddyemy@gmail.com>
"""
from typing import List
from flask import Flask, Blueprint

def register_blueprints(app: Flask) -> None:
    """Register all application blueprints, including API and docs."""
    # Lazy imports to avoid circulars during app factory
    from .core.api import create_api_blueprint
    from .core.api.v1 import create_api_v1_blueprint
    from .core.api.v1.admin import create_api_v1_admin_blueprint
    from .core.api.v1.public import create_api_v1_public_blueprint
    from .error_handlers.api import attach_api_err_handlers

    # Create the blueprints
    api_bp = create_api_blueprint()
    v1_api = create_api_v1_blueprint()
    v1_admin_api = create_api_v1_admin_blueprint()
    v1_public_api = create_api_v1_public_blueprint()
    
    # Attach JSON error handlers to all API scopes BEFORE registration
    attach_api_err_handlers(api_bp)
    attach_api_err_handlers(v1_api)
    attach_api_err_handlers(v1_admin_api)
    attach_api_err_handlers(v1_public_api)
    
    # Register sub-blueprints under /api/v1
    register_sub_blueprints(v1_api, [v1_admin_api, v1_public_api])
    
    # Register versioned API blueprints
    register_sub_blueprints(api_bp, [v1_api])

    # Register the root API blueprint
    app.register_blueprint(api_bp)


def register_sub_blueprints(bp: Blueprint, blueprints: List[Blueprint]):
    for sub_bp in blueprints:
        bp.register_blueprint(sub_bp)