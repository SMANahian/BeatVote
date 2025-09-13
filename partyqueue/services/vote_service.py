class VoteService:
    @staticmethod
    def vote(song: dict, user_id: str, vote: str) -> dict:
        likes = set(song.get("likes", []))
        dislikes = set(song.get("dislikes", []))
        if vote == "like":
            dislikes.discard(user_id)
            likes.add(user_id)
        elif vote == "dislike":
            likes.discard(user_id)
            dislikes.add(user_id)
        elif vote == "clear":
            likes.discard(user_id)
            dislikes.discard(user_id)
        else:
            raise ValueError("invalid vote")
        song["likes"] = list(likes)
        song["dislikes"] = list(dislikes)
        song["score"] = len(likes) - len(dislikes)
        return song
