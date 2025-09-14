from datetime import datetime, timezone
from . import ObjectId


def insert_song(
    coll,
    room_id: str,
    video_id: str,
    title: str,
    thumbnail_url: str,
    duration_sec: int,
    added_by_user_id: str | None,
    added_by_display_name: str,
) -> dict:
    song = {
        "_id": ObjectId(),
        "room_id": room_id,
        "video_id": video_id,
        "title": title,
        "thumbnail_url": thumbnail_url,
        "duration_sec": duration_sec,
        "added_by_user_id": added_by_user_id,
        "added_by_display_name": added_by_display_name,
        "added_at": datetime.now(timezone.utc),
        "likes": [],
        "dislikes": [],
        "score": 0,
        "played": False,
        "removed_by_host": False,
        "removed_at": None,
    }
    coll.insert_one(song)
    return song


def get_queue(coll, room_id: str) -> list[dict]:
    songs = list(coll.find({"room_id": room_id}))
    return sorted(
        [
            s
            for s in songs
            if not s.get("played") and not s.get("removed_by_host")
        ],
        key=lambda s: (-s.get("score", 0), s["added_at"]),
    )
