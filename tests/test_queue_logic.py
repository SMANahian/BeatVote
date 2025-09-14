from datetime import datetime, timedelta, timezone

from partyqueue.services.queue_service import QueueService
from partyqueue.services.vote_service import VoteService


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
    next_song = QueueService.get_next_song(room, queue)
    assert next_song["_id"] == s2["_id"]
    assert room["current_song_id"] == s2["_id"]
