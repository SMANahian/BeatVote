from flask import Flask, jsonify, redirect, request, url_for
from .config import Config
from .extensions import mongo, login_manager
from .routes.auth import auth_bp
from .routes.rooms import rooms_bp
from .routes.api import api_bp
from .models import ROOMS_COLL, SONGS_COLL, USERS_COLL


def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    mongo.init_app(app)
    mongo.db[USERS_COLL].create_index("username", unique=True)
    mongo.db[USERS_COLL].create_index("email", unique=True)
    mongo.db[ROOMS_COLL].create_index("host_user_id", unique=True)
    mongo.db[ROOMS_COLL].create_index("code_listener", unique=True)
    mongo.db[ROOMS_COLL].create_index("code_suggestor", unique=True)
    mongo.db[SONGS_COLL].create_index(
        [("room_id", 1), ("played", 1), ("removed_by_host", 1)]
    )
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    @login_manager.unauthorized_handler
    def _unauthorized():
        if request.path.startswith("/api/"):
            return jsonify({"error": "auth required"}), 401
        return redirect(url_for("auth.login"))

    return app


app = create_app()


if __name__ == "__main__":
    app.run()
