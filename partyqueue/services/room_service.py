from datetime import datetime


def is_video_allowed(room: dict, video_id: str) -> bool:
    return video_id not in room.get("banned_video_ids", []) and video_id not in room.get("deleted_video_ids", [])


def ban_video(room: dict, video_id: str) -> None:
    if video_id not in room.setdefault("banned_video_ids", []):
        room["banned_video_ids"].append(video_id)


def unban_video(room: dict, video_id: str) -> None:
    room["banned_video_ids"] = [v for v in room.get("banned_video_ids", []) if v != video_id]


def mark_deleted(room: dict, song: dict) -> None:
    room.setdefault("deleted_video_ids", []).append(song["video_id"])
    song["removed_by_host"] = True
    song["removed_at"] = datetime.utcnow()
