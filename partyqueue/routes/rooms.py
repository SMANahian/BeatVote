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
        name = request.form.get("name", "My Party")
        room = room_model.create_room(mongo.db[ROOMS_COLL], name, current_user.id)
        return redirect(url_for("rooms.host", room_id=room["_id"]))
    return render_template("host_room.html")


@rooms_bp.route("/<room_id>/host")
@login_required
def host(room_id):
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id})
    return render_template("host_room.html", room=room)


@rooms_bp.route("/<room_id>/guest")
def guest(room_id):
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id})
    return render_template("guest_room.html", room=room)


@rooms_bp.route("/join")
def join_page():
    return render_template("join_room.html")
