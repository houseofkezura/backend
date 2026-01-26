from flask import Blueprint

bp = Blueprint("waitlist", __name__, url_prefix="/waitlist")

from . import routes
