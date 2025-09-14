from datetime import datetime, timezone
from . import ObjectId


def insert_message(
    coll, room_id: str, sender_id: str | None, sender_name: str, message: str
) -> str:
    doc = {
        "_id": ObjectId(),
        "room_id": room_id,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "message": message,
        "created_at": datetime.now(timezone.utc),
    }
    coll.insert_one(doc)
    return doc["_id"]
