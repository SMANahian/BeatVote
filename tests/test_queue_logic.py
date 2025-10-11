from datetime import datetime, timedelta, timezone

from bson import ObjectId
from flask import Flask

from beatvote.services.queue_service import QueueService
from beatvote.services.vote_service import VoteService
from beatvote.routes.api import get_queue
from beatvote.extensions import mongo
from beatvote.models import SONGS_COLL, ROOMS_COLL


class DummyCollection:
    def __init__(self, docs):
        self._docs = [doc.copy() for doc in docs]

    def find_one(self, query):
        for doc in self._docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc.copy()
        return None

    def find(self, query):
        for doc in self._docs:
            if all(doc.get(k) == v for k, v in query.items()):
                yield doc.copy()


def test_queue_ordering():
    room = {"banned_video_ids": [], "deleted_video_ids": []}
    queue = []
    now = datetime.now(timezone.utc)
    s1 = QueueService.add_song(
        room, queue, {"video_id": "a", "title": "A", "added_at": now}
    )
    s2 = QueueService.add_song(
        room,
        queue,
        {
            "video_id": "b",
            "title": "B",
            "added_at": now + timedelta(seconds=1),
        },
    )
    s3 = QueueService.add_song(
        room,
        queue,
        {
            "video_id": "c",
            "title": "C",
            "added_at": now + timedelta(seconds=2),
        },
    )

    VoteService.vote(s1, "u1", "like")
    VoteService.vote(s2, "u2", "like")
    VoteService.vote(s3, "u3", "like")
    ordered = QueueService.order_queue(queue)
    assert [s["video_id"] for s in ordered] == ["a", "b", "c"]

    VoteService.vote(s3, "u4", "like")
    ordered = QueueService.order_queue(queue)
    assert ordered[0]["video_id"] == "c"


def test_auto_advance():
    room = {
        "banned_video_ids": [],
        "deleted_video_ids": [],
        "current_song_id": None,
    }
    queue = []
    now = datetime.now(timezone.utc)
    s1 = QueueService.add_song(
        room, queue, {"video_id": "a", "title": "A", "added_at": now}
    )
    s2 = QueueService.add_song(
        room,
        queue,
        {
            "video_id": "b",
            "title": "B",
            "added_at": now + timedelta(seconds=1),
        },
    )
    VoteService.vote(s1, "u1", "like")
    VoteService.vote(s2, "u2", "dislike")
    next_song = QueueService.get_next_song(room, queue)
    assert next_song["video_id"] == "a"
    room["current_song_id"] = None
    VoteService.vote(s1, "u3", "dislike")  # score 0
    VoteService.vote(s2, "u4", "dislike")  # score -2
    next_song = QueueService.get_next_song(room, queue)
    assert next_song["video_id"] == "a"
    room["current_song_id"] = None
    VoteService.vote(s1, "u5", "dislike")  # score -1
    next_song = QueueService.get_next_song(room, queue)
    assert next_song is None


def test_skips_played_song():
    room = {"banned_video_ids": [], "deleted_video_ids": [], "current_song_id": None}
    queue = []
    now = datetime.now(timezone.utc)
    s1 = QueueService.add_song(room, queue, {"video_id": "a", "title": "A", "added_at": now})
    s2 = QueueService.add_song(room, queue, {"video_id": "b", "title": "B", "added_at": now})
    room["current_song_id"] = s1["_id"]
    s1["played"] = True
    s1["playing"] = False
    next_song = QueueService.get_next_song(room, queue)
    assert next_song["_id"] == s2["_id"]
    assert room["current_song_id"] == s2["_id"]


def test_next_song_does_not_depend_on_previous_id():
    now = datetime.now(timezone.utc)
    room = {"banned_video_ids": [], "deleted_video_ids": [], "current_song_id": "stale"}
    queue = []
    s1 = QueueService.add_song(room, queue, {"video_id": "a", "title": "A", "added_at": now})
    s2 = QueueService.add_song(
        room,
        queue,
        {"video_id": "b", "title": "B", "added_at": now + timedelta(seconds=1)},
    )
    next_song = QueueService.get_next_song(room, queue)
    assert next_song["_id"] == s1["_id"]
    assert room["current_song_id"] == s1["_id"]


def test_queue_excludes_currently_playing():
    room = {"banned_video_ids": [], "deleted_video_ids": []}
    queue = []
    now = datetime.now(timezone.utc)
    s1 = QueueService.add_song(room, queue, {"video_id": "a", "title": "A", "added_at": now})
    s2 = QueueService.add_song(
        room,
        queue,
        {"video_id": "b", "title": "B", "added_at": now + timedelta(seconds=1)},
    )
    s1["playing"] = True
    ordered = QueueService.order_queue(queue)
    assert [s["_id"] for s in ordered] == [s2["_id"]]


def test_get_queue_returns_current_song_when_stored_as_objectid(monkeypatch):
    app = Flask(__name__)
    room_id = "room42"
    song_oid = ObjectId()
    now = datetime.now(timezone.utc)
    room_doc = {"_id": room_id, "current_song_id": song_oid}
    song_doc = {
        "_id": song_oid,
        "room_id": room_id,
        "video_id": "xyz",
        "title": "Next Up",
        "score": 0,
        "added_at": now,
        "playing": True,
        "played": False,
        "removed_by_host": False,
    }
    dummy_db = {
        ROOMS_COLL: DummyCollection([room_doc]),
        SONGS_COLL: DummyCollection([song_doc]),
    }
    monkeypatch.setattr(mongo, "db", dummy_db, raising=False)

    with app.app_context():
        response = get_queue(room_id)

    data = response.get_json()
    assert data["current_song_id"] == str(song_oid)
    assert data["current_song"]["_id"] == str(song_oid)
    assert data["current_song"]["title"] == "Next Up"
