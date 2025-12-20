from flask import Blueprint

bp: Blueprint = Blueprint("web_admin_settings", __name__, url_prefix="/settings")

from . import routes as settings_routes