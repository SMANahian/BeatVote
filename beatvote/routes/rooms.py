from __future__ import annotations

from pathlib import Path

from flask import Blueprint, current_app, render_template, send_from_directory

rooms_bp = Blueprint("rooms", __name__)


def _serve_spa():
    """Serve the React SPA if built; otherwise fall back to legacy templates."""
    app_dir = Path(current_app.static_folder) / "app"
    index_path = app_dir / "index.html"
    if index_path.exists():
        return send_from_directory(app_dir, "index.html")
    return render_template("spa_missing.html")


@rooms_bp.get("/")
def landing():
    return _serve_spa()


@rooms_bp.get("/login")
def spa_login():
    return _serve_spa()


@rooms_bp.get("/signup")
def spa_signup():
    return _serve_spa()


@rooms_bp.get("/host")
def spa_host():
    return _serve_spa()


@rooms_bp.get("/join")
def spa_join():
    return _serve_spa()


@rooms_bp.get("/create")
def spa_create():
    return _serve_spa()


@rooms_bp.get("/<room_id>/host")
def spa_room_host(room_id: str):
    return _serve_spa()


@rooms_bp.get("/<room_id>/guest")
def spa_room_guest(room_id: str):
    return _serve_spa()
