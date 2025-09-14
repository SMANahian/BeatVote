import os
from datetime import timedelta


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    MONGO_URI = os.getenv("MONGO_URI") or os.getenv(
        "MONGODB_URI", "mongodb://localhost:27017/beatvote"
    )
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    SUGGEST_COOLDOWN_SEC = int(os.getenv("SUGGEST_COOLDOWN_SEC", "20"))
    VOTE_COOLDOWN_SEC = int(os.getenv("VOTE_COOLDOWN_SEC", "2"))
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")
