from flask import Blueprint

bp = Blueprint("admin_staff", __name__, url_prefix="/staff")

from . import routes








