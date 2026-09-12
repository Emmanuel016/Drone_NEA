"""
Main routes for the DroneNEA GUI.
"""
from flask import Blueprint, render_template, jsonify, current_app
from drone.config import config

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Render the main index page."""
    return render_template('index.html', config=config)