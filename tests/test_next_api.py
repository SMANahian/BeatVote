from datetime import datetime, timezone

from partyqueue.app import create_app
from partyqueue.extensions import mongo, socketio
from partyqueue.models import SONGS_COLL, ROOMS_COLL


def test_advance_queue_endpoint(monkeypatch):
    room_id = "r1"
    now = datetime.now(timezone.utc)
    songs_docs = [
        {
            "_id": "s1",
            "room_id": room_id,
            "video_id": "a",
            "title": "A",
            "added_at": now,
            "likes": [],
            "dislikes": [],
            "score": 0,
            "played": False,
            "removed_by_host": False,
        },
        {
            "_id": "s2",
            "room_id": room_id,
            "video_id": "b",
            "title": "B",
            "added_at": now,
            "likes": [],
            "dislikes": [],
            "score": 0,
            "played": False,
            "removed_by_host": False,
        },
    ]
    room_doc = {
        "_id": room_id,
        "current_song_id": None,
        "banned_video_ids": [],
        "deleted_video_ids": [],
    }

    class SongsColl:
        def find(self, query):
            return [s.copy() for s in songs_docs if s["room_id"] == query.get("room_id")]

        def update_one(self, query, update):
            for s in songs_docs:
                if s["_id"] == query["_id"]:
                    s.update(update["$set"])

    class RoomsColl:
        def find_one(self, query):
            if query.get("_id") == room_doc["_id"]:
                return room_doc
            return None

        def update_one(self, query, update):
            if query.get("_id") == room_doc["_id"]:
                room_doc.update(update["$set"])

    dummy_db = {SONGS_COLL: SongsColl(), ROOMS_COLL: RoomsColl()}
    monkeypatch.setattr(mongo, "db", dummy_db, raising=False)
    monkeypatch.setattr(socketio, "emit", lambda *a, **k: None)

    app = create_app()
    client = app.test_client()

    resp = client.post(f"/api/rooms/{room_id}/next")
    assert resp.status_code == 200
    assert resp.get_json()["video_id"] == "a"
    # The first call merely sets the current song without marking it as
    # played yet. The song should only be flagged once the next track is
    # requested.
    assert songs_docs[0]["played"] is False

    resp = client.post(f"/api/rooms/{room_id}/next")
    assert resp.status_code == 200
    assert resp.get_json()["video_id"] == "b"
    # After advancing again, the first song is marked as played and the
    # second song becomes current.
    assert songs_docs[0]["played"] is True
    assert room_doc["current_song_id"] == "s2"
