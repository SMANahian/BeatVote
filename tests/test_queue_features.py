from datetime import datetime, timedelta, timezone
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from partyqueue.services.queue_service import QueueService
from partyqueue.models import songs as songs_model


def test_add_song_duplicate_returns_none():
    room = {"banned_video_ids": [], "deleted_video_ids": []}
    queue = []
    first = QueueService.add_song(room, queue, {"video_id": "x", "title": "X"})
    assert first is not None
    assert QueueService.add_song(room, queue, {"video_id": "x", "title": "X"}) is None


def test_get_next_song_advances_and_marks_previous():
    room = {
        "banned_video_ids": [],
        "deleted_video_ids": [],
        "current_song_id": None,
    }
    queue = []
    s1 = QueueService.add_song(room, queue, {"video_id": "a", "title": "A"})
    s2 = QueueService.add_song(room, queue, {"video_id": "b", "title": "B"})
    first = QueueService.get_next_song(room, queue)
    assert first["_id"] == s1["_id"]
    second = QueueService.get_next_song(room, queue)
    assert second["_id"] == s2["_id"]
    assert s1["played"] is True


class FakeColl:
    def __init__(self, songs):
        self.songs = songs

    def find(self, query):
        def match(song):
            for k, v in query.items():
                if song.get(k) != v:
                    return False
            return True

        return [s.copy() for s in self.songs if match(s)]


def test_get_queue_handles_missing_flags_and_orders():
    now = datetime.now(timezone.utc)
    songs = [
        {"_id": "1", "room_id": "r1", "title": "A", "added_at": now, "score": 0},
        {
            "_id": "2",
            "room_id": "r1",
            "title": "B",
            "added_at": now + timedelta(seconds=1),
            "score": 1,
        },
        {
            "_id": "3",
            "room_id": "r1",
            "title": "C",
            "added_at": now + timedelta(seconds=2),
            "score": 0,
            "removed_by_host": True,
        },
        {"_id": "4", "room_id": "r2", "title": "D", "added_at": now, "score": 5},
    ]
    coll = FakeColl(songs)
    queue = songs_model.get_queue(coll, "r1")
    assert [s["_id"] for s in queue] == ["2", "1"]
