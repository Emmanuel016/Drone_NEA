"""
Test suite for DroneController model.
Tests drone control operations and state management.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.models.drone_controller import DroneController

class TestDroneController(unittest.TestCase):
    """Test cases for DroneController class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.controller = DroneController()
        self.assertFalse(self.controller._connected)
    
    @patch('gui.models.drone_controller.Drone')
    def test_initialization(self, mock_drone_class):
        """Test DroneController initialization."""
        mock_drone = Mock()
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        
        self.assertIsNotNone(controller.drone)
        self.assertFalse(controller._connected)
        mock_drone_class.assert_called_once()
    
    @patch('gui.models.drone_controller.Drone')
    def test_connect_success(self, mock_drone_class):
        """Test successful connection."""
        mock_drone = Mock()
        mock_drone.Start.return_value = True
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        result = controller.connect("udpin:0.0.0.0:14551")
        
        self.assertTrue(result)
        self.assertTrue(controller._connected)
        mock_drone.Start.assert_called_once()
    
    @patch('gui.models.drone_controller.Drone')
    def test_connect_failure(self, mock_drone_class):
        """Test connection failure."""
        mock_drone = Mock()
        mock_drone.Start.return_value = False
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        result = controller.connect("udpin:0.0.0.0:14551")
        
        self.assertFalse(result)
        self.assertFalse(controller._connected)
    
    @patch('gui.models.drone_controller.Drone')
    def test_connect_exception(self, mock_drone_class):
        """Test connection with exception."""
        mock_drone = Mock()
        mock_drone.Start.side_effect = Exception("Connection error")
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        
        with self.assertRaises(Exception) as context:
            controller.connect("udpin:0.0.0.0:14551")
        
        self.assertIn("Connection failed", str(context.exception))
    
    @patch('gui.models.drone_controller.Drone')
    def test_disconnect(self, mock_drone_class):
        """Test disconnection."""
        mock_drone = Mock()
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        controller._connected = True
        
        result = controller.disconnect()
        
        self.assertTrue(result)
        self.assertFalse(controller._connected)
        mock_drone.shutdown.assert_called_once()
    
    @patch('gui.models.drone_controller.Drone')
    def test_arm_when_connected(self, mock_drone_class):
        """Test arming when connected."""
        mock_drone = Mock()
        mock_drone.control = Mock()
        mock_drone.control.arm.return_value = True
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        controller._connected = True
        
        result = controller.arm()
        
        self.assertTrue(result)
        mock_drone.control.arm.assert_called_once()
    
    @patch('gui.models.drone_controller.Drone')
    def test_arm_when_not_connected(self, mock_drone_class):
        """Test arming when not connected."""
        mock_drone = Mock()
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        controller._connected = False
        
        with self.assertRaises(Exception) as context:
            controller.arm()
        
        self.assertIn("not connected", str(context.exception))
    
    @patch('gui.models.drone_controller.Drone')
    def test_disarm(self, mock_drone_class):
        """Test disarming."""
        mock_drone = Mock()
        mock_drone.control = Mock()
        mock_drone.control.disarm.return_value = True
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        controller._connected = True
        
        result = controller.disarm()
        
        self.assertTrue(result)
        mock_drone.control.disarm.assert_called_once()
    
    @patch('gui.models.drone_controller.Drone')
    def test_takeoff(self, mock_drone_class):
        """Test takeoff."""
        mock_drone = Mock()
        mock_drone.control = Mock()
        mock_drone.control.takeoff.return_value = True
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        controller._connected = True
        
        result = controller.takeoff(10.0)
        
        self.assertTrue(result)
        mock_drone.control.takeoff.assert_called_once_with(10.0)
    
    @patch('gui.models.drone_controller.Drone')
    def test_land(self, mock_drone_class):
        """Test landing."""
        mock_drone = Mock()
        mock_drone.control = Mock()
        mock_drone.control.land.return_value = True
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        controller._connected = True
        
        result = controller.land()
        
        self.assertTrue(result)
        mock_drone.control.land.assert_called_once()
    
    @patch('gui.models.drone_controller.Drone')
    def test_set_mode(self, mock_drone_class):
        """Test setting flight mode."""
        mock_drone = Mock()
        mock_drone.control = Mock()
        mock_drone.control.set_mode.return_value = True
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        controller._connected = True
        
        result = controller.set_mode("GUIDED")
        
        self.assertTrue(result)
        mock_drone.control.set_mode.assert_called_once_with("GUIDED")
    
    @patch('gui.models.drone_controller.Drone')
    def test_list_missions(self, mock_drone_class):
        """Test listing missions."""
        mock_drone = Mock()
        mock_planner = Mock()
        mock_planner.list_missions.return_value = ["mission1", "mission2"]
        mock_drone.mission_planner = mock_planner
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        
        missions = controller.list_missions()
        
        self.assertEqual(missions, ["mission1", "mission2"])
        mock_planner.list_missions.assert_called_once()
    
    @patch('gui.models.drone_controller.Drone')
    def test_list_missions_no_planner(self, mock_drone_class):
        """Test listing missions when no planner exists."""
        mock_drone = Mock()
        mock_drone.mission_planner = None
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        
        missions = controller.list_missions()
        
        self.assertEqual(missions, [])
    
    @patch('gui.models.drone_controller.Drone')
    def test_get_status(self, mock_drone_class):
        """Test getting drone status."""
        mock_drone = Mock()
        mock_drone.connection = Mock()
        mock_drone.connection.connection_string = "udpin:0.0.0.0:14551"
        mock_drone.control = Mock()
        mock_drone.control.is_armed.return_value = False
        mock_drone.control.get_mode.return_value = "GUIDED"
        mock_drone._initialized = True
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        controller._connected = True
        
        status = controller.get_status()
        
        self.assertTrue(status['connected'])
        self.assertTrue(status['initialized'])
        self.assertEqual(status['connection_string'], "udpin:0.0.0.0:14551")
        self.assertFalse(status['armed'])
        self.assertEqual(status['mode'], "GUIDED")
    
    @patch('gui.models.drone_controller.Drone')
    def test_get_status_not_connected(self, mock_drone_class):
        """Test getting status when not connected."""
        mock_drone = Mock()
        mock_drone.connection = Mock()
        mock_drone.connection.connection_string = None
        mock_drone._initialized = False
        mock_drone_class.return_value = mock_drone
        
        controller = DroneController()
        controller._connected = False
        
        status = controller.get_status()
        
        self.assertFalse(status['connected'])
        self.assertFalse(status['initialized'])
        self.assertIsNone(status['connection_string'])
        self.assertFalse(status['armed'])
        self.assertEqual(status['mode'], 'Unknown')


if __name__ == '__main__':
    unittest.main()