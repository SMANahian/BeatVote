"""Database collection helpers."""
from uuid import uuid4


def ObjectId() -> str:
    return uuid4().hex


USERS_COLL = "users"
ROOMS_COLL = "rooms"
SONGS_COLL = "songs"
CHATS_COLL = "chats"

__all__ = ["ObjectId", "USERS_COLL", "ROOMS_COLL", "SONGS_COLL", "CHATS_COLL"]
