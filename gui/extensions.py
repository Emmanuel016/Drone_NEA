"""
Flask extensions initialization.
This module initializes and configures Flask extensions used in the application.
"""

from flask_socketio import SocketIO

# Initialize SocketIO without an app - will be initialized in app factory
socketio = SocketIO(cors_allowed_origins="*")


def init_extensions(app):
    """Initialize Flask extensions with the application."""
    socketio.init_app(app, cors_allowed_origins=app.config['SOCKETIO_CORS_ALLOWED_ORIGINS'])
    return socketio
