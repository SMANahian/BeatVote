import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from partyqueue.services.vote_service import VoteService


def test_vote_flipping():
    song = {"likes": [], "dislikes": [], "score": 0}
    VoteService.vote(song, "u1", "like")
    assert song["likes"] == ["u1"] and song["score"] == 1
    VoteService.vote(song, "u1", "dislike")
    assert song["dislikes"] == ["u1"] and song["score"] == -1
    VoteService.vote(song, "u1", "clear")
    assert song["likes"] == [] and song["dislikes"] == [] and song["score"] == 0
