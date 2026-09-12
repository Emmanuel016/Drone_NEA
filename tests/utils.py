"""
Shared test utilities and helpers for DroneNEA tests.
This module provides common functionality used across different test files.
"""
import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def setup_test_logging(log_name: str, log_dir: Path = None):
    """
    Setup logging configuration for tests.
    
    Args:
        log_name: Name of the log file
        log_dir: Directory to store log files (defaults to project logs directory)
    
    Returns:
        Configured logger instance
    """
    if log_dir is None:
        log_dir = project_root / "logs"
    
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / log_name),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def get_project_root():
    """Get the project root directory."""
    return project_root

def get_log_dir():
    """Get the logs directory."""
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    return log_dir

def get_mission_dir():
    """Get the missions directory."""
    mission_dir = project_root / "missions"
    mission_dir.mkdir(exist_ok=True)
    return mission_dir
