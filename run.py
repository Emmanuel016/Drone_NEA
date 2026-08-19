"""
Entry point for running the DroneNEA Flask application.
"""

import os
from gui import create_app
from drone.config import setup_logging

# Setup centralized logging
setup_logging()

# Get configuration from environment variable or use default
config_name = os.environ.get('FLASK_CONFIG', 'default')

# Create the application instance
app, socketio = create_app(config_name)

if __name__ == '__main__':
    # Get server settings from config
    host = app.config.get('HOST', '0.0.0.0')
    port = app.config.get('PORT', 5000)
    debug = app.config.get('DEBUG', True)
    
    print(f"[DroneNEA GUI] Starting server on {host}:{port} (debug={debug})")
    socketio.run(app, host=host, port=port, debug=debug)
