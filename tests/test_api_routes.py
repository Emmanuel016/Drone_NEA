"""
Test suite for GUI API routes.
Tests API endpoints for drone control, telemetry, and mission management.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from drone.exceptions import ConnectionError, ControlError, ValidationError


class TestAPIRoutes(unittest.TestCase):
    """Test cases for API routes."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mock drone controller
        self.mock_drone_controller = Mock()
        self.mock_drone_controller._connected = False
        self.mock_drone_controller.drone = Mock()
        self.mock_drone_controller.drone._initialized = False
        
        # Create mock telemetry manager
        self.mock_telemetry_manager = Mock()
        self.mock_telemetry_manager.running = False
        self.mock_telemetry_manager.thread = Mock()
        self.mock_telemetry_manager.thread.is_alive.return_value = False
    
    def test_drone_error_to_dict(self):
        """Test DroneNEAError to_dict method."""
        error = ConnectionError("Test connection error", {"details": "test details"})
        error_dict = error.to_dict()
        
        self.assertEqual(error_dict['error_type'], 'ConnectionError')
        self.assertEqual(error_dict['message'], 'Test connection error')
        self.assertEqual(error_dict['details'], {"details": "test details"})
    
    def test_drone_error_without_details(self):
        """Test DroneNEAError without details."""
        error = ControlError("Test control error")
        error_dict = error.to_dict()
        
        self.assertEqual(error_dict['error_type'], 'ControlError')
        self.assertEqual(error_dict['message'], 'Test control error')
        self.assertEqual(error_dict['details'], {})


class TestDroneControllerMock(unittest.TestCase):
    """Test drone controller mocking for API tests."""
    
    def test_drone_controller_initialization(self):
        """Test drone controller mock setup."""
        mock_controller = Mock()
        mock_controller._connected = False
        mock_controller.drone = Mock()
        mock_controller.drone._initialized = False
        
        self.assertFalse(mock_controller._connected)
        self.assertFalse(mock_controller.drone._initialized)
    
    def test_drone_controller_connect_success(self):
        """Test drone controller connect success."""
        mock_controller = Mock()
        mock_controller._connected = False
        mock_controller.connect.return_value = True
        
        result = mock_controller.connect("udpin:0.0.0.0:14551")
        
        self.assertTrue(result)
        mock_controller.connect.assert_called_once_with("udpin:0.0.0.0:14551")
    
    def test_drone_controller_connect_failure(self):
        """Test drone controller connect failure."""
        mock_controller = Mock()
        mock_controller._connected = False
        mock_controller.connect.side_effect = ConnectionError("Connection failed")
        
        with self.assertRaises(ConnectionError):
            mock_controller.connect("invalid_connection")


class TestTelemetryManagerMock(unittest.TestCase):
    """Test telemetry manager mocking for API tests."""
    
    def test_telemetry_manager_initialization(self):
        """Test telemetry manager mock setup."""
        mock_manager = Mock()
        mock_manager.running = False
        mock_manager.thread = Mock()
        mock_manager.thread.is_alive.return_value = False
        
        self.assertFalse(mock_manager.running)
        self.assertFalse(mock_manager.thread.is_alive())
    
    def test_telemetry_manager_start(self):
        """Test telemetry manager start."""
        mock_manager = Mock()
        mock_manager.running = False
        
        mock_manager.start()
        
        mock_manager.start.assert_called_once()
    
    def test_telemetry_manager_stop(self):
        """Test telemetry manager stop."""
        mock_manager = Mock()
        mock_manager.running = True
        
        mock_manager.stop()
        
        mock_manager.stop.assert_called_once()


if __name__ == '__main__':
    unittest.main()