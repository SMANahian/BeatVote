from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, jsonify, make_response, request
from flask_login import current_user, login_user, logout_user
from pymongo.errors import DuplicateKeyError

from ..extensions import mongo
from ..models import CHATS_COLL, ObjectId, ROOMS_COLL, SONGS_COLL
from ..models import chats as chat_model
from ..models import rooms as room_model
from ..models import songs as song_model
from ..services import auth_service
from ..services import room_service
from ..services.permission_service import get_role, set_role
from ..services.queue_service import QueueService
from ..services.vote_service import VoteService
from ..services.youtube_service import search_videos

api_bp = Blueprint("api", __name__)

HOST_ACTIONS = {"host"}
SUGGEST_ACTIONS = {"host", "suggestor"}
VOTE_ACTIONS = {"host", "suggestor", "listener"}


def _actor_id() -> str | None:
    if current_user.is_authenticated:
        return current_user.id
    return request.cookies.get("guest_id")


def _actor_name() -> str:
    if current_user.is_authenticated:
        return current_user.username
    return request.cookies.get("guest_name") or "Guest"


def _room_or_404(room_id: str) -> dict | None:
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id})
    return room


def _role_for(room: dict, actor_id: str | None) -> str | None:
    if not actor_id:
        return None
    role = get_role(room, actor_id)
    if role:
        return role
    if current_user.is_authenticated and actor_id == room.get("host_user_id"):
        return "host"
    return None


def _require_role(room: dict, allowed: set[str]) -> tuple[str, str]:
    actor_id = _actor_id()
    if not actor_id:
        return "", ""
    role = _role_for(room, actor_id)
    if role not in allowed:
        return actor_id, ""
    return actor_id, role


def _iso(dt: Any) -> str | None:
    if not dt:
        return None
    if isinstance(dt, str):
        return dt
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    return str(dt)


def _serialize_song(song: dict, actor_id: str | None) -> dict:
    likes = set(song.get("likes", []))
    dislikes = set(song.get("dislikes", []))
    my_vote = None
    if actor_id:
        if actor_id in likes:
            my_vote = "like"
        elif actor_id in dislikes:
            my_vote = "dislike"
    return {
        "_id": str(song.get("_id")),
        "room_id": song.get("room_id"),
        "video_id": song.get("video_id"),
        "title": song.get("title"),
        "thumbnail_url": song.get("thumbnail_url"),
        "duration_sec": song.get("duration_sec"),
        "added_by_display_name": song.get("added_by_display_name"),
        "added_at": _iso(song.get("added_at")),
        "score": song.get("score", 0),
        "my_vote": my_vote,
        "played": bool(song.get("played")),
        "removed_by_host": bool(song.get("removed_by_host")),
        "removed_at": _iso(song.get("removed_at")),
    }


def _serialize_queue(room: dict, actor_id: str | None) -> dict:
    queue = list(mongo.db[SONGS_COLL].find({"room_id": room["_id"]}))
    ordered = QueueService.order_queue(queue)
    current = room.get("current_song_id")
    return {
        "queue": [_serialize_song(s, actor_id) for s in ordered],
        "current_song_id": str(current) if current else None,
    }


def _serialize_room(room: dict, actor_id: str | None) -> dict:
    role = _role_for(room, actor_id)
    payload = {
        "_id": room.get("_id"),
        "name": room.get("name"),
        "active": bool(room.get("active", True)),
        "role": role,
    }
    if role == "host" and current_user.is_authenticated:
        payload.update(
            {
                "code_listener": room.get("code_listener"),
                "code_suggestor": room.get("code_suggestor"),
                "host_token": room.get("host_token"),
            }
        )
    return payload


def _host_authorized(room: dict) -> bool:
    actor_id = _actor_id()
    if actor_id and _role_for(room, actor_id) == "host":
        return True
    token = request.headers.get("X-BeatVote-Host-Token")
    return bool(token and token == room.get("host_token"))


@api_bp.get("/health")
def health():
    return jsonify({"ok": True})


@api_bp.get("/me")
def me():
    if current_user.is_authenticated:
        return jsonify(
            {
                "authenticated": True,
                "user": {"id": current_user.id, "username": current_user.username},
            }
        )
    guest_id = request.cookies.get("guest_id")
    guest_name = request.cookies.get("guest_name")
    return jsonify(
        {"authenticated": False, "guest": {"id": guest_id, "name": guest_name}}
    )


@api_bp.post("/auth/login")
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"error": "missing fields"}), 400
    user = auth_service.authenticate(email, password)
    if not user:
        return jsonify({"error": "invalid credentials"}), 401
    login_user(user, remember=True)
    return jsonify({"user": {"id": user.id, "username": user.username}})


@api_bp.post("/auth/signup")
def api_signup():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not email or not username or not password:
        return jsonify({"error": "missing fields"}), 400
    try:
        user = auth_service.register(email, username, password)
    except DuplicateKeyError:
        return jsonify({"error": "email or username already exists"}), 409
    login_user(user, remember=True)
    return jsonify({"user": {"id": user.id, "username": user.username}})


@api_bp.post("/auth/logout")
def api_logout():
    if current_user.is_authenticated:
        logout_user()
    resp = make_response(jsonify({"ok": True}))
    return resp


@api_bp.post("/auth/guest")
def api_guest():
    data = request.get_json(silent=True) or {}
    name = (data.get("display_name") or "Guest").strip() or "Guest"
    guest_id = request.cookies.get("guest_id") or ObjectId()
    resp = make_response(jsonify({"guest": {"id": guest_id, "name": name}}))
    resp.set_cookie("guest_id", guest_id, httponly=True, samesite="Lax")
    resp.set_cookie("guest_name", name, httponly=False, samesite="Lax")
    return resp


@api_bp.post("/rooms")
def create_room():
    if not current_user.is_authenticated:
        return jsonify({"error": "auth required"}), 401
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "My Party").strip() or "My Party"
    existing = mongo.db[ROOMS_COLL].find_one({"host_user_id": current_user.id})
    if existing:
        return jsonify({"room": _serialize_room(existing, current_user.id)}), 200
    room = room_model.create_room(mongo.db[ROOMS_COLL], name, current_user.id)
    return jsonify({"room": _serialize_room(room, current_user.id)}), 201


@api_bp.get("/rooms/mine")
def my_room():
    if not current_user.is_authenticated:
        return jsonify({"error": "auth required"}), 401
    room = mongo.db[ROOMS_COLL].find_one({"host_user_id": current_user.id})
    if not room:
        return jsonify({"room": None}), 200
    return jsonify({"room": _serialize_room(room, current_user.id)})


@api_bp.post("/rooms/join")
def join_room():
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip().upper()
    display_name = (data.get("display_name") or "Guest").strip() or "Guest"
    if not code:
        return jsonify({"error": "missing code"}), 400
    room = room_model.find_by_code(mongo.db[ROOMS_COLL], code)
    if not room:
        return jsonify({"error": "invalid code"}), 404

    if current_user.is_authenticated:
        actor_id = current_user.id
    else:
        actor_id = request.cookies.get("guest_id") or ObjectId()

    role = "listener" if code.startswith("L-") else "suggestor"
    set_role(room, actor_id, role)
    mongo.db[ROOMS_COLL].update_one(
        {"_id": room["_id"]}, {"$set": {f"roles.{actor_id}": role}}
    )

    resp = make_response(jsonify({"room": _serialize_room(room, actor_id)}))
    if not current_user.is_authenticated:
        resp.set_cookie("guest_id", actor_id, httponly=True, samesite="Lax")
        resp.set_cookie("guest_name", display_name, httponly=False, samesite="Lax")
    return resp


@api_bp.get("/rooms/<room_id>")
def get_room(room_id: str):
    room = _room_or_404(room_id)
    if not room:
        return jsonify({"error": "not found"}), 404
    actor_id = _actor_id()
    return jsonify({"room": _serialize_room(room, actor_id)})


@api_bp.get("/youtube/search")
def youtube_search():
    q = (request.args.get("q") or "").strip()
    room_id = (request.args.get("room_id") or "").strip()
    if not q:
        return jsonify({"error": "missing query"}), 400
    if not room_id:
        return jsonify({"error": "missing room_id"}), 400
    room = _room_or_404(room_id)
    if not room:
        return jsonify({"error": "room not found"}), 404
    actor_id = _actor_id()
    if _role_for(room, actor_id) not in SUGGEST_ACTIONS:
        return jsonify({"error": "insufficient permissions"}), 403
    try:
        results = search_videos(q)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:  # requests errors, missing key, etc
        return jsonify({"error": "youtube lookup failed", "detail": str(e)}), 502
    return jsonify({"results": results})


@api_bp.get("/rooms/<room_id>/queue")
def get_queue(room_id):
    room = _room_or_404(room_id)
    if not room:
        return jsonify({"error": "room not found"}), 404
    actor_id = _actor_id()
    return jsonify(_serialize_queue(room, actor_id))


@api_bp.post("/rooms/<room_id>/queue/add")
def add_song(room_id):
    room = _room_or_404(room_id)
    if not room:
        return jsonify({"error": "room not found"}), 404

    actor_id, role = _require_role(room, SUGGEST_ACTIONS)
    if not actor_id:
        return jsonify({"error": "guest identity required"}), 401
    if not role:
        return jsonify({"error": "insufficient permissions"}), 403

    data = request.get_json(silent=True) or {}
    video_id = (data.get("video_id") or "").strip()
    title = (data.get("title") or "").strip()
    thumbnail_url = (data.get("thumbnail_url") or "").strip() or None
    duration_sec = data.get("duration_sec")
    if isinstance(duration_sec, str) and duration_sec.isdigit():
        duration_sec = int(duration_sec)
    if duration_sec is not None and not isinstance(duration_sec, int):
        duration_sec = None
    if not video_id or not title:
        return jsonify({"error": "missing fields"}), 400

    if not room.get("active", True):
        return jsonify({"error": "room inactive"}), 400
    if not room_service.is_video_allowed(room, video_id):
        return jsonify({"error": "video not allowed"}), 403

    existing = mongo.db[SONGS_COLL].find_one(
        {
            "room_id": room_id,
            "video_id": video_id,
            "played": False,
            "removed_by_host": False,
        }
    )
    if existing:
        return get_queue(room_id)

    added_by_user_id = current_user.id if current_user.is_authenticated else None
    display_name = _actor_name()

    song_model.insert_song(
        mongo.db[SONGS_COLL],
        room_id=room_id,
        video_id=video_id,
        title=title,
        thumbnail_url=thumbnail_url or "",
        duration_sec=duration_sec or 0,
        added_by_user_id=added_by_user_id,
        added_by_display_name=display_name,
    )
    return get_queue(room_id)


@api_bp.post("/rooms/<room_id>/queue/<song_id>/vote")
def vote_song(room_id, song_id):
    room = _room_or_404(room_id)
    if not room:
        return jsonify({"error": "room not found"}), 404

    actor_id, role = _require_role(room, VOTE_ACTIONS)
    if not actor_id:
        return jsonify({"error": "guest identity required"}), 401
    if not role:
        return jsonify({"error": "join room first"}), 403

    data = request.get_json(silent=True) or {}
    vote = data.get("vote")
    if vote not in {"like", "dislike", "clear"}:
        return jsonify({"error": "invalid vote"}), 400

    song = mongo.db[SONGS_COLL].find_one({"_id": song_id, "room_id": room_id})
    if not song:
        return jsonify({"error": "not found"}), 404
    if song.get("played") or song.get("removed_by_host"):
        return jsonify({"error": "song no longer votable"}), 400

    VoteService.vote(song, actor_id, vote)
    mongo.db[SONGS_COLL].update_one(
        {"_id": song_id},
        {
            "$set": {
                "likes": song["likes"],
                "dislikes": song["dislikes"],
                "score": song["score"],
            }
        },
    )
    return get_queue(room_id)


@api_bp.post("/rooms/<room_id>/queue/<song_id>/remove")
def remove_song(room_id, song_id):
    room = _room_or_404(room_id)
    if not room:
        return jsonify({"error": "room not found"}), 404
    if not _host_authorized(room):
        return jsonify({"error": "host authorization required"}), 403

    song = mongo.db[SONGS_COLL].find_one({"_id": song_id, "room_id": room_id})
    if not song:
        return jsonify({"error": "not found"}), 404

    removed_at = song.get("removed_at") or datetime.now(timezone.utc)
    mongo.db[SONGS_COLL].update_one(
        {"_id": song_id},
        {"$set": {"removed_by_host": True, "removed_at": removed_at}},
    )

    deleted_ids = list(room.get("deleted_video_ids", []))
    if song["video_id"] not in deleted_ids:
        deleted_ids.append(song["video_id"])
    mongo.db[ROOMS_COLL].update_one(
        {"_id": room_id},
        {"$set": {"deleted_video_ids": deleted_ids}},
    )
    return get_queue(room_id)


@api_bp.post("/rooms/<room_id>/queue/<song_id>/play")
def play_song(room_id, song_id):
    room = _room_or_404(room_id)
    if not room:
        return jsonify({"error": "room not found"}), 404
    if not _host_authorized(room):
        return jsonify({"error": "host authorization required"}), 403

    song = mongo.db[SONGS_COLL].find_one({"_id": song_id, "room_id": room_id})
    if not song:
        return jsonify({"error": "not found"}), 404
    if song.get("removed_by_host") or song.get("played"):
        return jsonify({"error": "song not playable"}), 400

    mongo.db[ROOMS_COLL].update_one(
        {"_id": room_id}, {"$set": {"current_song_id": song_id}}
    )
    return get_queue(room_id)


@api_bp.post("/rooms/<room_id>/queue/next")
def next_song(room_id):
    """Mark the current song as played and advance to the next one."""
    room = _room_or_404(room_id)
    if not room:
        return jsonify({"error": "room not found"}), 404
    if not _host_authorized(room):
        return jsonify({"error": "host authorization required"}), 403

    current_id = room.get("current_song_id")
    if current_id:
        mongo.db[SONGS_COLL].update_one({"_id": current_id}, {"$set": {"played": True}})
        mongo.db[ROOMS_COLL].update_one(
            {"_id": room_id}, {"$set": {"current_song_id": None}}
        )

    room["current_song_id"] = None
    queue = list(mongo.db[SONGS_COLL].find({"room_id": room_id}))
    QueueService.get_next_song(room, queue)
    mongo.db[ROOMS_COLL].update_one(
        {"_id": room_id}, {"$set": {"current_song_id": room.get("current_song_id")}}
    )
    return get_queue(room_id)


@api_bp.get("/rooms/<room_id>/chat")
def get_chat(room_id: str):
    room = _room_or_404(room_id)
    if not room:
        return jsonify({"error": "room not found"}), 404
    actor_id = _actor_id()
    if _role_for(room, actor_id) not in VOTE_ACTIONS:
        return jsonify({"error": "join room first"}), 403

    after = request.args.get("after")
    query: dict[str, Any] = {"room_id": room_id}
    if after:
        query["_id"] = {"$gt": after}
    msgs = list(
        mongo.db[CHATS_COLL].find(query).sort("created_at", 1).limit(100)
    )
    payload = [
        {
            "_id": str(m.get("_id")),
            "sender_name": m.get("sender_name"),
            "message": m.get("message"),
            "created_at": _iso(m.get("created_at")),
        }
        for m in msgs
    ]
    return jsonify({"messages": payload})


@api_bp.post("/rooms/<room_id>/chat")
def post_chat(room_id: str):
    room = _room_or_404(room_id)
    if not room:
        return jsonify({"error": "room not found"}), 404
    actor_id = _actor_id()
    if _role_for(room, actor_id) not in VOTE_ACTIONS:
        return jsonify({"error": "join room first"}), 403

    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "missing message"}), 400
    if len(message) > 500:
        return jsonify({"error": "message too long"}), 400

    msg_id = chat_model.insert_message(
        mongo.db[CHATS_COLL],
        room_id=room_id,
        sender_id=actor_id,
        sender_name=_actor_name(),
        message=message,
    )
    return jsonify({"message_id": msg_id}), 201
