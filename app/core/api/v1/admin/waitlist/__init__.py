from flask import Blueprint

bp = Blueprint("admin_waitlist", __name__, url_prefix="/waitlist")

from . import routes
