from flask import Blueprint

def create_api_v1_blueprint():
    """Blueprint root for API v1."""
    api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/v1")

    # Ensure route modules are imported so view functions are registered
    import app.core.api.v1.public  # noqa: F401,E402
    import app.core.api.v1.admin  # noqa: F401,E402

    return api_v1_bp
