from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..services.youtube_service import search_videos
from ..services.queue_service import QueueService
from ..extensions import mongo, socketio
from ..models import SONGS_COLL, ROOMS_COLL

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
    return jsonify(ordered)


@api_bp.post("/rooms/<room_id>/next")
def advance_queue(room_id):
    """Advance the room's queue and return the next song if available."""
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id})
    if not room:
        return jsonify({"error": "room not found"}), 404

    queue = list(mongo.db[SONGS_COLL].find({"room_id": room_id}))
    next_song = QueueService.get_next_song(room, queue)

    # Persist room state and mark played songs
    mongo.db[ROOMS_COLL].update_one(
        {"_id": room_id}, {"$set": {"current_song_id": room.get("current_song_id")}}
    )
    for s in queue:
        if s.get("played"):
            mongo.db[SONGS_COLL].update_one(
                {"_id": s["_id"]}, {"$set": {"played": True}}
            )

    # Notify listeners that the queue changed
    ordered = QueueService.order_queue(queue)
    for s in ordered:
        s["_id"] = str(s["_id"])
    socketio.emit("queue:updated", ordered, room=room_id, namespace="/room")

    if next_song:
        next_song["_id"] = str(next_song["_id"])
        return jsonify(next_song), 200
    return jsonify({}), 204
