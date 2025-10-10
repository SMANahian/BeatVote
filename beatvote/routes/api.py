from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..services.youtube_service import search_videos
from copy import deepcopy

from ..services.queue_service import QueueService
from ..services.vote_service import VoteService
from ..extensions import mongo
from ..models import SONGS_COLL, ROOMS_COLL
from datetime import datetime, timezone

api_bp = Blueprint("api", __name__)


@api_bp.get("/youtube/search")
@login_required
def youtube_search():
    q = request.args.get("q", "")
    results = search_videos(q)
    return jsonify(results)


@api_bp.get("/rooms/<room_id>/queue")
def _serialize_song(song: dict | None) -> dict | None:
    if not song:
        return None
    serialized = deepcopy(song)
    if "_id" in serialized:
        serialized["_id"] = str(serialized["_id"])
    return serialized


def get_queue(room_id):
    queue = list(mongo.db[SONGS_COLL].find({"room_id": room_id}))
    ordered = QueueService.order_queue(queue)
    for s in ordered:
        s["_id"] = str(s["_id"])
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id}) or {}
    current_song_data = room.get("current_song")
    current = room.get("current_song_id")
    current_song = None
    current_id_str = None
    if current_song_data:
        current_song = _serialize_song(current_song_data)
    elif current:
        current_song = mongo.db[SONGS_COLL].find_one(
            {"_id": current, "room_id": room_id}
        )
        current_song = _serialize_song(current_song)
    if current_song and not current:
        current = current_song.get("_id")
    if current:
        current_id_str = str(current)
    return jsonify(
        {
            "queue": ordered,
            "current_song_id": current_id_str,
            "current_song": current_song,
        }
    )


@api_bp.post("/rooms/<room_id>/queue/add")
def add_song(room_id):
    data = request.get_json() or {}
    video_id = data.get("video_id")
    title = data.get("title")
    user_id = (
        current_user.id
        if current_user.is_authenticated
        else request.cookies.get("guest_id")
    )
    if not all([video_id, title, user_id]):
        return jsonify({"error": "missing fields"}), 400
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id}) or {}
    queue = list(mongo.db[SONGS_COLL].find({"room_id": room_id}))
    song = {
        "room_id": room_id,
        "video_id": video_id,
        "title": title,
        "added_by": user_id,
    }
    added = QueueService.add_song(room, queue, song)
    if added is song:
        mongo.db[SONGS_COLL].insert_one(song)
    return get_queue(room_id)


@api_bp.post("/rooms/<room_id>/queue/<song_id>/vote")
def vote_song(room_id, song_id):
    data = request.get_json() or {}
    vote = data.get("vote")
    user_id = (
        current_user.id
        if current_user.is_authenticated
        else request.cookies.get("guest_id")
    )
    if not all([vote, user_id]):
        return jsonify({"error": "missing fields"}), 400
    song = mongo.db[SONGS_COLL].find_one({"_id": song_id, "room_id": room_id})
    if not song:
        return jsonify({"error": "not found"}), 404
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id}) or {}
    if room.get("current_song_id") == song_id or song.get("playing"):
        return jsonify({"error": "song is currently playing"}), 400
    if song.get("played"):
        return jsonify({"error": "song already played"}), 400
    VoteService.vote(song, user_id, vote)
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
    song = mongo.db[SONGS_COLL].find_one({"_id": song_id, "room_id": room_id})
    if not song:
        return jsonify({"error": "not found"}), 404
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id}) or {}
    QueueService.delete_song(room, [song], song_id)
    mongo.db[SONGS_COLL].update_one(
        {"_id": song_id},
        {
            "$set": {
                "removed_by_host": True,
                "removed_at": song.get("removed_at", datetime.now(timezone.utc)),
            }
        },
    )
    mongo.db[ROOMS_COLL].update_one(
        {"_id": room_id},
        {"$set": {"deleted_video_ids": room.get("deleted_video_ids", [])}},
    )
    return get_queue(room_id)


@api_bp.post("/rooms/<room_id>/queue/<song_id>/play")
def play_song(room_id, song_id):
    song = mongo.db[SONGS_COLL].find_one({"_id": song_id, "room_id": room_id})
    if not song:
        return jsonify({"error": "not found"}), 404
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id}) or {}
    current_id = room.get("current_song_id")
    now = datetime.now(timezone.utc)
    if current_id and current_id != song_id:
        mongo.db[ROOMS_COLL].update_one(
            {"_id": room_id},
            {
                "$set": {
                    "last_finished_song": room.get("current_song"),
                    "current_song": None,
                    "current_song_id": None,
                    "last_finished_at": now,
                }
            },
        )
    mongo.db[SONGS_COLL].delete_one({"_id": song_id})
    song_payload = deepcopy(song)
    song_payload["_id"] = song_id
    song_payload["started_at"] = now
    mongo.db[ROOMS_COLL].update_one(
        {"_id": room_id},
        {
            "$set": {
                "current_song_id": song_id,
                "current_song": song_payload,
            }
        },
    )
    return get_queue(room_id)


@api_bp.post("/rooms/<room_id>/queue/next")
def next_song(room_id):
    """Mark the current song as played and advance to the next one."""
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id}) or {}
    now = datetime.now(timezone.utc)
    update_doc: dict = {
        "current_song_id": None,
        "current_song": None,
        "last_finished_song": room.get("current_song"),
        "last_finished_at": now,
    }
    mongo.db[ROOMS_COLL].update_one(
        {"_id": room_id},
        {"$set": update_doc},
    )
    queue = list(mongo.db[SONGS_COLL].find({"room_id": room_id}))
    next_up = QueueService.get_next_song(room, queue)
    new_current_id = next_up["_id"] if next_up else None
    room["current_song_id"] = new_current_id
    if next_up:
        mongo.db[SONGS_COLL].delete_one({"_id": next_up["_id"]})
        next_payload = deepcopy(next_up)
        next_payload["started_at"] = now
        next_payload["_id"] = next_up["_id"]
        mongo.db[ROOMS_COLL].update_one(
            {"_id": room_id},
            {
                "$set": {
                    "current_song_id": new_current_id,
                    "current_song": next_payload,
                }
            },
        )
    return get_queue(room_id)
