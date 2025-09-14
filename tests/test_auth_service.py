import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from bson import ObjectId
from beatvote.services import auth_service
from beatvote.extensions import mongo
from beatvote.models import USERS_COLL


class DummyCollection:
    def __init__(self, doc):
        self._doc = doc

    def find_one(self, query):
        # simulate MongoDB lookup by _id
        return self._doc if query.get("_id") == self._doc["_id"] else None


def test_load_user_converts_objectid(monkeypatch):
    user_doc = {"_id": ObjectId(), "email": "e@example.com", "username": "e"}
    dummy_db = {USERS_COLL: DummyCollection(user_doc)}
    # replace the mongo.db with our dummy mapping
    monkeypatch.setattr(mongo, "db", dummy_db, raising=False)

    loaded = auth_service.load_user(str(user_doc["_id"]))
    assert loaded is not None
    assert loaded.id == str(user_doc["_id"])
