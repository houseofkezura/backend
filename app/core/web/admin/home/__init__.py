from flask import Blueprint

bp: Blueprint = Blueprint("web_admin_home", __name__, url_prefix="")

from . import routes as home_routes