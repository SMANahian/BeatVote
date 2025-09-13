from flask import Flask
from .config import Config
from .extensions import mongo, socketio, login_manager
from .routes.auth import auth_bp
from .routes.rooms import rooms_bp
from .routes.api import api_bp
from .sockets.events import register_socketio_events


def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    mongo.init_app(app)
    socketio.init_app(app, async_mode="eventlet", cors_allowed_origins="*")
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    register_socketio_events(socketio)

    return app


app = create_app()


if __name__ == "__main__":
    socketio.run(app)
