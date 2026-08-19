"""
Configuration settings for the DroneNEA Flask application.
"""

import os


class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'drone-nea-secret-key-change-in-production'
    
    # Flask-SocketIO settings
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    
    # Server settings
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
