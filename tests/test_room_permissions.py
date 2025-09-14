import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from beatvote.services.queue_service import QueueService
from beatvote.services import room_service


def test_ban_and_delete_logic():
    room = {"banned_video_ids": [], "deleted_video_ids": []}
    queue = []
    # add song and delete
    song = QueueService.add_song(room, queue, {"video_id": "v1", "title": "V1"})
    QueueService.delete_song(room, queue, song["_id"])
    assert QueueService.add_song(room, queue, {"video_id": "v1", "title": "V1"}) is None

    # ban second song
    room_service.ban_video(room, "v2")
    assert QueueService.add_song(room, queue, {"video_id": "v2", "title": "V2"}) is None
    room_service.unban_video(room, "v2")
    assert QueueService.add_song(room, queue, {"video_id": "v2", "title": "V2"}) is not None
