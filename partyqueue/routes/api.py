from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ..services.youtube_service import search_videos
from ..services.queue_service import QueueService
from ..extensions import mongo
from ..models import SONGS_COLL

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
