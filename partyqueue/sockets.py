from flask import request
from flask_socketio import join_room
from flask_login import current_user

from .extensions import socketio, mongo
from .models import SONGS_COLL, ROOMS_COLL
from .services.queue_service import QueueService
from .services.vote_service import VoteService


def _emit_queue(room_id: str) -> None:
    queue = list(mongo.db[SONGS_COLL].find({"room_id": room_id}))
    ordered = QueueService.order_queue(queue)
    for s in ordered:
        s["_id"] = str(s["_id"])
    socketio.emit(
        "queue:updated", ordered, room=room_id, namespace="/room"
    )


@socketio.on("room:join", namespace="/room")
def on_join(data):
    room_id = data.get("room_id")
    if not room_id:
        return
    join_room(room_id)
    _emit_queue(room_id)
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id})
    if room and room.get("current_song_id"):
        current = mongo.db[SONGS_COLL].find_one(
            {"_id": room["current_song_id"]}
        )
        if current:
            socketio.emit(
                "player:play",
                {"video_id": current["video_id"]},
                room=request.sid,
                namespace="/room",
            )


@socketio.on("queue:add", namespace="/room")
def on_queue_add(data):
    room_id = data.get("room_id")
    video_id = data.get("video_id")
    title = data.get("title")
    if not room_id or not video_id or not title:
        return
    room = mongo.db[ROOMS_COLL].find_one({"_id": room_id})
    if not room:
        return
    queue = list(mongo.db[SONGS_COLL].find({"room_id": room_id}))
    song = {
        "room_id": room_id,
        "video_id": video_id,
        "title": title,
        "added_by_user_id": getattr(current_user, "id", None),
        "added_by_display_name": getattr(current_user, "username", "Anon"),
    }
    new_song = QueueService.add_song(room, queue, song)
    if not new_song:
        return
    mongo.db[SONGS_COLL].insert_one(new_song)
    if not room.get("current_song_id"):
        mongo.db[ROOMS_COLL].update_one(
            {"_id": room_id}, {"$set": {"current_song_id": new_song["_id"]}}
        )
        socketio.emit(
            "player:play",
            {"video_id": video_id},
            room=room_id,
            namespace="/room",
        )
    _emit_queue(room_id)


@socketio.on("queue:vote", namespace="/room")
def on_queue_vote(data):
    room_id = data.get("room_id")
    song_id = data.get("song_id")
    vote = data.get("vote")
    if not room_id or not song_id or not vote:
        return
    song = mongo.db[SONGS_COLL].find_one({"_id": song_id})
    if not song:
        return
    user_id = getattr(current_user, "id", request.sid)
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
    _emit_queue(room_id)
