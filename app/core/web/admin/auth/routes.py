from __future__ import annotations

from urllib.parse import quote
from flask import current_app, render_template, request, url_for, redirect, flash, make_response

from . import bp


def _build_clerk_sign_in_url(redirect_url: str) -> str:
    """
    Build Clerk hosted sign-in URL with redirect back to admin.
    """
    frontend_api = current_app.config.get("CLERK_FRONTEND_API")
    if not frontend_api:
        raise RuntimeError("CLERK_FRONTEND_API is not configured")

    base = frontend_api.rstrip("/")
    if not base.startswith("http://") and not base.startswith("https://"):
        base = f"https://{base}"

    return f"{base}/sign-in?redirect_url={quote(redirect_url, safe='')}"


@bp.route("/login", methods=["GET"])
def login():
    """
    Redirect users to Clerk hosted sign-in. No local form needed.
    """
    redirect_target = request.args.get(
        "next", url_for("web.web_admin.web_admin_home.index", _external=True)
    )

    publishable_key = current_app.config.get("CLERK_PUBLISHABLE_KEY")
    sign_in_url = None

    if not publishable_key:
        flash("Clerk publishable key is missing. Contact an administrator.", "error")
    else:
        # Keep hosted sign-in as a fallback link if needed
        try:
            sign_in_url = _build_clerk_sign_in_url(redirect_target)
        except RuntimeError:
            sign_in_url = None

    return render_template(
        "admin/pages/auth/login.html",
        sign_in_url=sign_in_url,
        clerk_publishable_key=publishable_key,
        redirect_target=redirect_target,
    )


@bp.route("/register", methods=["GET"])
def register_redirect():
    """
    No public signup for admin UI. Redirect to login.
    """
    return redirect(url_for("web.web_admin.web_admin_auth.login"))


@bp.route("/logout", methods=["GET"])
def logout():
    """
    Render a small page that triggers Clerk client sign-out and redirects to the admin login.
    This ensures the Clerk session cookie is cleared client-side; we also redirect back to login.
    """
    publishable_key = current_app.config.get("CLERK_PUBLISHABLE_KEY")
    login_url = url_for("web.web_admin.web_admin_auth.login", _external=True)
    resp = make_response(render_template("admin/pages/auth/logout.html", clerk_publishable_key=publishable_key, login_url=login_url))
    # Clear common Clerk cookies to prevent lingering sessions
    cookie_domain = request.host.split(":")[0] if request.host else None
    for cookie_name in ("__session", "clerk_session", "__clerk"):
        resp.delete_cookie(cookie_name, path="/")
        if cookie_domain:
            resp.delete_cookie(cookie_name, path="/", domain=cookie_domain)
    return resp
