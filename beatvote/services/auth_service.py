"""Authentication helpers."""

from flask_login import UserMixin
from bson import ObjectId
from bson.errors import InvalidId

from ..extensions import mongo, login_manager
from ..models import USERS_COLL
from ..models import users as user_model

class User(UserMixin):
    def __init__(self, user_doc: dict):
        self.id = str(user_doc["_id"])
        self.email = user_doc["email"]
        self.username = user_doc["username"]

@login_manager.user_loader
def load_user(user_id: str):
    """Load a user from the session ID.

    The session stores the user's MongoDB ``ObjectId`` as a string. When
    loading the user we must convert it back to ``ObjectId`` so that the lookup
    succeeds. Without this conversion, authentication would always fail on
    subsequent requests, resulting in ``Unauthorized`` errors after login.
    """

    try:
        oid = ObjectId(user_id)
    except InvalidId:
        return None
    doc = mongo.db[USERS_COLL].find_one({"_id": oid})
    return User(doc) if doc else None

def authenticate(email: str, password: str) -> User | None:
    user = user_model.find_user_by_email(mongo.db[USERS_COLL], email)
    if user and user_model.check_password(user, password):
        return User(user)
    return None

def register(email: str, username: str, password: str) -> User:
    uid = user_model.create_user(mongo.db[USERS_COLL], email, username, password)
    from bson import ObjectId
    if not isinstance(uid, ObjectId):
        uid = ObjectId(uid)
    user = mongo.db[USERS_COLL].find_one({"_id": uid})
    return User(user)
