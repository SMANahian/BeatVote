from datetime import datetime, timezone
import random
import secrets
import string
from . import ObjectId

CODE_CHARS = string.ascii_uppercase


def _generate_code(prefix: str, length: int = 4) -> str:
    return f"{prefix}-" + "".join(random.choices(CODE_CHARS, k=length))


def _generate_unique_code(coll, field: str, prefix: str) -> str:
    for _ in range(25):
        code = _generate_code(prefix)
        if coll.find_one({field: code}) is None:
            return code
    raise RuntimeError(f"failed to generate unique room code for {field}")


def create_room(coll, name: str, host_user_id: str) -> dict:
    room = {
        "_id": ObjectId(),
        "name": name,
        "host_user_id": host_user_id,
        "host_token": secrets.token_urlsafe(32),
        "code_listener": _generate_unique_code(coll, "code_listener", "L"),
        "code_suggestor": _generate_unique_code(coll, "code_suggestor", "S"),
        "active": True,
        "created_at": datetime.now(timezone.utc),
        "deleted_video_ids": [],
        "banned_video_ids": [],
        "current_song_id": None,
        "player_state": {},
        "roles": {host_user_id: "host"},
    }
    coll.insert_one(room)
    return room


def find_by_code(coll, code: str) -> dict | None:
    if code.startswith("L-"):
        return coll.find_one({"code_listener": code})
    if code.startswith("S-"):
        return coll.find_one({"code_suggestor": code})
    return None
