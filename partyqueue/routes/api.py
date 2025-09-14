from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..services.youtube_service import search_videos
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
def get_queue(room_id):
    queue = list(mongo.db[SONGS_COLL].find({"room_id": room_id}))
    ordered = QueueService.order_queue(queue)
    for s in ordered:
        s["_id"] = str(s["_id"])
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id}) or {}
    current = room.get("current_song_id")
    if current:
        current = str(current)
    return jsonify({"queue": ordered, "current_song_id": current})


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
    mongo.db[ROOMS_COLL].update_one(
        {"_id": room_id},
        {"$set": {"current_song_id": song_id}},
    )
    return get_queue(room_id)
