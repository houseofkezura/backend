from __future__ import annotations

from flask import Blueprint, redirect, url_for

from . import bp

@bp.route("/", methods=["GET"])
def index():
    return redirect(url_for("api.index")) #Leave Like this for now