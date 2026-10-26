"""Staff login / logout (Flask-Login)."""
from urllib.parse import urljoin, urlparse

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import User

auth = Blueprint("auth", __name__)

# Compared against when the email is unknown, so response time doesn't reveal valid emails.
_DUMMY_HASH = generate_password_hash("not-a-real-password")
GENERIC_ERROR = "Incorrect email or password."


def is_safe_redirect(target):
    """Only allow redirects back to this same site (blocks open-redirect attacks)."""
    if not target:
        return False
    host = urlparse(request.host_url)
    dest = urlparse(urljoin(request.host_url, target))
    return dest.scheme in ("http", "https") and dest.netloc == host.netloc


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    error = None
    email = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter(func.lower(User.email) == email).first()
        password_ok = check_password_hash(user.password_hash if user else _DUMMY_HASH, password)
        if user and password_ok:
            login_user(user)
            target = request.args.get("next")
            return redirect(target if is_safe_redirect(target) else url_for("admin.dashboard"))
        error = GENERIC_ERROR

    return render_template("auth/login.html", error=error, email=email), (401 if error else 200)


@auth.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("public.home"))
