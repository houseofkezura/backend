from flask import Blueprint

bp = Blueprint("admin_users", __name__, url_prefix="/users")

from . import routes







