from flask_socketio import join_room, leave_room, emit
from . import queue_service
from ..services import vote_service

# in-memory store for demo
_queues = {}
_rooms = {}


def register_socketio_events(socketio):
    @socketio.on("join_room", namespace="/room")
    def handle_join(data):
        room_id = data["room_id"]
        join_room(room_id)
        emit("presence:update", {"room_id": room_id}, to=room_id)

    @socketio.on("leave_room", namespace="/room")
    def handle_leave(data):
        room_id = data["room_id"]
        leave_room(room_id)
        emit("presence:update", {"room_id": room_id}, to=room_id)

    @socketio.on("queue:add", namespace="/room")
    def handle_add(data):
        room_id = data["room_id"]
        room = _rooms.setdefault(room_id, {"banned_video_ids": [], "deleted_video_ids": [], "current_song_id": None})
        queue = _queues.setdefault(room_id, [])
        song = {
            "video_id": data["video_id"],
            "title": data.get("title", ""),
            "thumbnail_url": data.get("thumbnail_url", ""),
            "duration_sec": data.get("duration_sec", 0),
            "added_by_display_name": data.get("added_by", ""),
        }
        queue_service.QueueService.add_song(room, queue, song)
        emit("queue:updated", queue_service.QueueService.order_queue(queue), to=room_id)

    @socketio.on("vote", namespace="/room")
    def handle_vote(data):
        room_id = data["room_id"]
        user_id = data["user_id"]
        song_id = data["song_id"]
        queue = _queues.setdefault(room_id, [])
        for s in queue:
            if str(s["_id"]) == song_id:
                vote_service.VoteService.vote(s, user_id, data["vote"])
                break
        emit("queue:updated", queue_service.QueueService.order_queue(queue), to=room_id)
