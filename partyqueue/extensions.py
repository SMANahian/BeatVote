from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_socketio import SocketIO

mongo = PyMongo()
login_manager = LoginManager()
socketio = SocketIO(async_mode="eventlet")
