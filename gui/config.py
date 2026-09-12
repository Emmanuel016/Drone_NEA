"""
Configuration settings for the DroneNEA Flask application.
"""
from dotenv import load_dotenv
import os
load_dotenv()
class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set")
    
    # Flask-SocketIO settings
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5000').split(',')
    
    # Server settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    DEBUG = False
    
    # Security settings
    API_KEY = os.environ.get('API_KEY')
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', '60'))


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    # Allow all locally for development
    SOCKETIO_CORS_ALLOWED_ORIGINS = "*"
    # Disable rate limiting in development
    RATE_LIMIT_ENABLED = False
    # Use a default secret key for development only
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    # Require API key in production
    if not os.environ.get('API_KEY'):
        raise ValueError("API_KEY environment variable must be set in production")


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

