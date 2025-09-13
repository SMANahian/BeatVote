from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.collection import Collection


def create_user(coll: Collection, email: str, username: str, password: str) -> str:
    doc = {
        "email": email,
        "username": username,
        "password_hash": generate_password_hash(password),
        "created_at": datetime.utcnow(),
        "current_rooms_owned": [],
    }
    result = coll.insert_one(doc)
    return str(result.inserted_id)


def find_user_by_email(coll: Collection, email: str) -> dict | None:
    return coll.find_one({"email": email})


def check_password(user: dict, password: str) -> bool:
    return check_password_hash(user["password_hash"], password)
