from flask import Blueprint

bp: Blueprint = Blueprint("web_public_home", __name__, url_prefix="")

from . import routes as home_routes