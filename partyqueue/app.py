import eventlet

eventlet.monkey_patch()

from flask import Flask  # noqa: E402
from .config import Config  # noqa: E402
from .extensions import mongo, login_manager, socketio  # noqa: E402
from .routes.auth import auth_bp  # noqa: E402
from .routes.rooms import rooms_bp  # noqa: E402
from .routes.api import api_bp  # noqa: E402


def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    mongo.init_app(app)
    mongo.db.users.create_index("username", unique=True)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    app.register_blueprint(auth_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    from . import sockets  # noqa: F401

    return app


app = create_app()


if __name__ == "__main__":
    socketio.run(app)
