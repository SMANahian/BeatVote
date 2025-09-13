ROLES = {"host", "suggestor", "listener"}


def get_role(room: dict, user_id: str) -> str | None:
    return room.get("roles", {}).get(user_id)


def set_role(room: dict, user_id: str, role: str) -> None:
    if role not in ROLES:
        raise ValueError("invalid role")
    room.setdefault("roles", {})[user_id] = role


def require_role(room: dict, user_id: str, required: str) -> bool:
    return get_role(room, user_id) == required
