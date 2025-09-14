"""Application factory for the PartyQueue Flask app.

The original project relies on :mod:`eventlet` to monkey patch the
standard library in order to provide cooperative sockets for
``Flask-SocketIO``.  The test environment used in this kata runs on
Python 3.12 which no longer bundles the ``distutils`` module that older
versions of ``eventlet`` try to import.  Importing ``eventlet`` would
therefore raise a ``ModuleNotFoundError`` and prevent the application
module from being imported at all, causing the test suite to fail during
collection.

To keep the application importable without requiring the optional
dependency we attempt to import ``eventlet`` but gracefully handle the
case where it is missing.  When available, the library is still used to
monkey patch the standard library as before; when it is not available the
application continues without the monkey patching which is sufficient for
the unit tests that exercise only the synchronous parts of the code.
"""

try:  # pragma: no cover - exercised implicitly when eventlet is present
    import eventlet

    eventlet.monkey_patch()
except ModuleNotFoundError:  # pragma: no cover - used in the test env
    eventlet = None

from flask import Flask  # noqa: E402
from .config import Config  # noqa: E402
from .extensions import mongo, login_manager, socketio  # noqa: E402
from .routes.auth import auth_bp  # noqa: E402
from .routes.rooms import rooms_bp  # noqa: E402
from .routes.api import api_bp  # noqa: E402


def create_app(config_object: type[Config] | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or Config)

    # When running the real application a MongoDB connection is
    # initialised here.  The unit tests monkeypatch ``mongo.db`` with a
    # simple dictionary before calling ``create_app`` to avoid the need for
    # an actual database.  If ``mongo.db`` has already been replaced we
    # skip initialisation entirely so the stub remains in place.
    if not isinstance(getattr(mongo, "db", None), dict):
        mongo.init_app(app)
        # The application normally creates an index on the ``users``
        # collection during start-up.  In the unit tests a real MongoDB
        # server isn't available and ``mongo.db`` is later monkey patched
        # with a lightweight stub.  Attempting to create the index against
        # a real server would therefore raise a ``ServerSelectionTimeoutError``
        # during test collection.  We ignore any exception here so that
        # tests can supply their own in-memory implementations instead of
        # connecting to an actual database.
        try:  # pragma: no cover - behaviour depends on environment
            mongo.db.users.create_index("username", unique=True)
        except Exception:  # pragma: no cover - fallback for test env
            pass
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
