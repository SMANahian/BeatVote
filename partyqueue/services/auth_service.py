"""Authentication helpers."""
from flask_login import UserMixin
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
    doc = mongo.db[USERS_COLL].find_one({"_id": user_id})
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
