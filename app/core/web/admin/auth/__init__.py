from flask import Blueprint

bp: Blueprint = Blueprint("web_admin_auth", __name__, url_prefix="")

from . import routes  # noqa: E402,F401

