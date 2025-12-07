from flask import Blueprint

bp = Blueprint("admin_crm", __name__, url_prefix="/crm")

from . import routes

