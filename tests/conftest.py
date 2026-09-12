"""
Shared pytest fixtures and configuration for all tests.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

@pytest.fixture(scope="session")
def project_root():
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

@pytest.fixture(scope="session")
def log_dir(project_root):
    """Get the logs directory."""
    log_path = project_root / "logs"
    log_path.mkdir(exist_ok=True)
    return log_path

@pytest.fixture(scope="session")
def mission_dir(project_root):
    """Get the missions directory."""
    mission_path = project_root / "missions"
    mission_path.mkdir(exist_ok=True)
    return mission_path
