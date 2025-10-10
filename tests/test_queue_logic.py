from copy import deepcopy
from datetime import datetime, timedelta, timezone

from bson import ObjectId
from flask import Flask

from beatvote.services.queue_service import QueueService
from beatvote.services.vote_service import VoteService
from beatvote.routes.api import get_queue, next_song, play_song
from beatvote.extensions import mongo
from beatvote.models import SONGS_COLL, ROOMS_COLL


class InMemoryCollection:
    def __init__(self, docs=None):
        self._docs = [deepcopy(doc) for doc in docs or []]

    @staticmethod
    def _matches(doc, query):
        return all(doc.get(k) == v for k, v in query.items())

    def find_one(self, query):
        for doc in self._docs:
            if self._matches(doc, query):
                return deepcopy(doc)
        return None

    def find(self, query):
        for doc in self._docs:
            if self._matches(doc, query):
                yield deepcopy(doc)

    def insert_one(self, doc):
        self._docs.append(deepcopy(doc))

    def delete_one(self, query):
        for idx, doc in enumerate(self._docs):
            if self._matches(doc, query):
                self._docs.pop(idx)
                return

    def update_one(self, query, update):
        for doc in self._docs:
            if self._matches(doc, query):
                if "$set" in update:
                    for key, value in update["$set"].items():
                        doc[key] = deepcopy(value)
                if "$unset" in update:
                    for key in update["$unset"].keys():
                        doc.pop(key, None)
                return


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


def test_next_song_skips_current_id_even_if_unplayed():
    now = datetime.now(timezone.utc)
    room = {"banned_video_ids": [], "deleted_video_ids": [], "current_song_id": None}
    queue = []
    s1 = QueueService.add_song(room, queue, {"video_id": "a", "title": "A", "added_at": now})
    s2 = QueueService.add_song(
        room,
        queue,
        {"video_id": "b", "title": "B", "added_at": now + timedelta(seconds=1)},
    )
    room["current_song_id"] = s1["_id"]
    s1["played"] = False
    s1["playing"] = False
    next_song = QueueService.get_next_song(room, queue)
    assert next_song["_id"] == s2["_id"]
    assert room["current_song_id"] == s2["_id"]


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
    room_doc = {
        "_id": room_id,
        "current_song_id": song_oid,
        "current_song": {
            "_id": str(song_oid),
            "room_id": room_id,
            "video_id": "xyz",
            "title": "Next Up",
            "score": 0,
            "added_at": now,
        },
    }
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
        ROOMS_COLL: InMemoryCollection([room_doc]),
        SONGS_COLL: InMemoryCollection([song_doc]),
    }
    monkeypatch.setattr(mongo, "db", dummy_db, raising=False)

    with app.app_context():
        response = get_queue(room_id)

    data = response.get_json()
    assert data["current_song_id"] == str(song_oid)
    assert data["current_song"]["_id"] == str(song_oid)
    assert data["current_song"]["title"] == "Next Up"


def test_play_song_removes_entry_from_queue(monkeypatch):
    app = Flask(__name__)
    room_id = "room99"
    song_id = "song-1"
    now = datetime.now(timezone.utc)
    room_doc = {"_id": room_id, "current_song_id": None, "current_song": None}
    song_doc = {
        "_id": song_id,
        "room_id": room_id,
        "video_id": "abc",
        "title": "Track A",
        "score": 5,
        "added_at": now,
    }
    dummy_db = {
        ROOMS_COLL: InMemoryCollection([room_doc]),
        SONGS_COLL: InMemoryCollection([song_doc]),
    }
    monkeypatch.setattr(mongo, "db", dummy_db, raising=False)

    with app.app_context():
        response = play_song(room_id, song_id)

    data = response.get_json()
    assert data["current_song"]["_id"] == song_id
    assert data["queue"] == []
    rooms = dummy_db[ROOMS_COLL]._docs
    assert rooms[0]["current_song_id"] == song_id
    assert rooms[0]["current_song"]["title"] == "Track A"
    assert dummy_db[SONGS_COLL].find_one({"_id": song_id}) is None


def test_next_song_advances_queue_and_deletes_previous(monkeypatch):
    app = Flask(__name__)
    room_id = "room88"
    current_song = {
        "_id": "song-1",
        "room_id": room_id,
        "video_id": "aaa",
        "title": "Current",
    }
    next_song_doc = {
        "_id": "song-2",
        "room_id": room_id,
        "video_id": "bbb",
        "title": "Next",
        "score": 1,
        "added_at": datetime.now(timezone.utc),
    }
    later_song_doc = {
        "_id": "song-3",
        "room_id": room_id,
        "video_id": "ccc",
        "title": "Later",
        "score": 0,
        "added_at": datetime.now(timezone.utc) + timedelta(seconds=10),
    }
    room_doc = {
        "_id": room_id,
        "current_song_id": current_song["_id"],
        "current_song": current_song,
    }
    dummy_db = {
        ROOMS_COLL: InMemoryCollection([room_doc]),
        SONGS_COLL: InMemoryCollection([next_song_doc, later_song_doc]),
    }
    monkeypatch.setattr(mongo, "db", dummy_db, raising=False)

    with app.app_context():
        response = next_song(room_id)

    data = response.get_json()
    assert data["current_song"]["_id"] == "song-2"
    assert data["current_song"]["title"] == "Next"
    remaining_queue_ids = [s["_id"] for s in data["queue"]]
    assert remaining_queue_ids == ["song-3"]
    rooms = dummy_db[ROOMS_COLL]._docs
    assert rooms[0]["current_song_id"] == "song-2"
    assert rooms[0]["last_finished_song"]["_id"] == "song-1"
    assert dummy_db[SONGS_COLL].find_one({"_id": "song-2"}) is None
