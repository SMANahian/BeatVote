from flask import Flask
from .config import Config
from .extensions import mongo, login_manager
from .routes.auth import auth_bp
from .routes.rooms import rooms_bp
from .routes.api import api_bp


def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    mongo.init_app(app)
    mongo.db.users.create_index("username", unique=True)
    login_manager.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    return app


app = create_app()


if __name__ == "__main__":
    app.run()
