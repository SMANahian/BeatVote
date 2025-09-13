from typing import List
from ..models import ObjectId
from datetime import datetime
from . import room_service


class QueueService:
    @staticmethod
    def add_song(room: dict, queue: List[dict], song: dict) -> dict | None:
        """Add song if allowed and not duplicate. Returns existing or new song."""
        if not room_service.is_video_allowed(room, song["video_id"]):
            return None
        for existing in queue:
            if existing["video_id"] == song["video_id"] and not existing.get("removed_by_host") and not existing.get("played"):
                return existing
        song.setdefault("_id", ObjectId())
        song.setdefault("added_at", datetime.utcnow())
        song.setdefault("likes", [])
        song.setdefault("dislikes", [])
        song.setdefault("score", 0)
        song.setdefault("played", False)
        song.setdefault("removed_by_host", False)
        queue.append(song)
        return song

    @staticmethod
    def delete_song(room: dict, queue: List[dict], song_id: str) -> None:
        for s in queue:
            if s["_id"] == song_id:
                room_service.mark_deleted(room, s)
                break

    @staticmethod
    def order_queue(queue: List[dict]) -> List[dict]:
        return sorted(
            [s for s in queue if not s.get("removed_by_host") and not s.get("played")],
            key=lambda s: (-s.get("score", 0), s["added_at"]),
        )

    @staticmethod
    def get_next_song(room: dict, queue: List[dict]) -> dict | None:
        ordered = QueueService.order_queue(queue)
        if ordered and ordered[0].get("score", 0) >= 0:
            room["current_song_id"] = ordered[0]["_id"]
            return ordered[0]
        return None
