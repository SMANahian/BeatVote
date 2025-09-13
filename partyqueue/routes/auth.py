from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_user, logout_user, login_required
import uuid
from ..services import auth_service

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        user = auth_service.authenticate(email, password)
        if user:
            login_user(user)
            return redirect(url_for("rooms.create"))
        flash("Invalid credentials", "error")
    return render_template("auth_login.html")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "")
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        user = auth_service.register(email, username, password)
        login_user(user)
        return redirect(url_for("rooms.create"))
    return render_template("auth_signup.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/guest", methods=["POST"])
def guest():
    name = request.form.get("display_name", "Guest") or "Guest"
    guest_id = str(uuid.uuid4())
    resp = make_response({"guest_id": guest_id, "display_name": name})
    resp.set_cookie("guest_id", guest_id)
    resp.set_cookie("guest_name", name)
    return resp
