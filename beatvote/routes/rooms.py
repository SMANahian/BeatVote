from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from ..extensions import mongo
from ..models import ROOMS_COLL
from ..models import rooms as room_model

rooms_bp = Blueprint("rooms", __name__)


@rooms_bp.route("/")
def landing():
    return render_template("landing_choose.html")


@rooms_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        existing_room = mongo.db[ROOMS_COLL].find_one({"host_user_id": current_user.id})
        if existing_room:
            return redirect(url_for("rooms.host_dashboard"))
        name = request.form.get("name", "My Party")
        room_model.create_room(mongo.db[ROOMS_COLL], name, current_user.id)
        return redirect(url_for("rooms.host_dashboard"))
    return redirect(url_for("rooms.host_dashboard"))


@rooms_bp.route("/host")
@login_required
def host_dashboard():
    room = mongo.db[ROOMS_COLL].find_one({"host_user_id": current_user.id})
    return render_template("host_room.html", room=room)


@rooms_bp.route("/<room_id>/host")
@login_required
def host(room_id):
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id})
    return render_template("host_room.html", room=room)


@rooms_bp.route("/<room_id>/guest")
def guest(room_id):
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id})
    role = request.args.get("role")
    return render_template("guest_room.html", room=room, role=role)

@rooms_bp.route("/join", methods=["GET", "POST"])
def join_page():
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        room = room_model.find_by_code(mongo.db[ROOMS_COLL], code)
        if room:
            role = "listener" if code.startswith("L-") else "suggestor"
            return redirect(url_for("rooms.guest", room_id=room["_id"], role=role))
        return render_template("join_room.html", error="Invalid code")
    return render_template("join_room.html")
