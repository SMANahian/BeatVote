from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_socketio import SocketIO

mongo = PyMongo()
login_manager = LoginManager()

# ``flask_socketio`` supports a variety of asynchronous modes.  The
# original project depends on ``eventlet`` but that dependency is optional
# for the tests where only the synchronous parts of the application are
# exercised.  Attempt to use ``eventlet`` when it is installed, otherwise
# fall back to the built-in ``threading`` mode so that the extension
# initialises successfully without additional packages.
try:  # pragma: no cover - depends on environment
    import eventlet  # noqa: F401

    async_mode = "eventlet"
except ModuleNotFoundError:  # pragma: no cover - test environment
    async_mode = "threading"

socketio = SocketIO(async_mode=async_mode)
