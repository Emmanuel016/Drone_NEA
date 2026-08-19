"""
GUI package for DroneNEA
Flask application factory for drone control web interface.
"""

from flask import Flask
from gui.config import config
from gui.extensions import init_extensions
from gui.routes import main_bp, api_bp
from gui.models import DroneController, TelemetryManager


def create_app(config_name='default'):
    """Application factory for creating Flask app instances."""
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    socketio = init_extensions(app)
    
    # Initialize drone controller and telemetry manager
    app.drone_controller = DroneController()
    app.telemetry_manager = TelemetryManager(socketio, app.drone_controller.drone)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    
    return app, socketio
