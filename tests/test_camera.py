"""
Test suite for camera.py module.
Tests MAVLink camera control functionality.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from drone.camera import Camera
from drone.connection import Connection
from drone.telemetry import Telemetry


class TestCamera(unittest.TestCase):
    """Test cases for Camera class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_connection = Mock(spec=Connection)
        self.mock_connection.is_connected.return_value = True
        self.mock_master = Mock()
        self.mock_master.target_system = 1
        self.mock_master.target_component = 200
        self.mock_connection.get_master.return_value = self.mock_master
        
        self.mock_telemetry = Mock(spec=Telemetry)
        
        self.camera = Camera(self.mock_connection, self.mock_telemetry)
    
    def test_camera_initialization(self):
        """Test camera initialization."""
        self.assertIsNotNone(self.camera.connection)
        self.assertIsNotNone(self.camera.telemetry)
        self.assertEqual(self.camera._camera_mode, "PHOTO")
        self.assertFalse(self.camera._is_recording)
    
    def test_take_photo_success(self):
        """Test successful photo capture."""
        self.camera.take_photo()
        
        # Verify MAVLink command was sent
        self.mock_master.mav.command_long_send.assert_called_once()
        
        # Check command parameters
        call_args = self.mock_master.mav.command_long_send.call_args
        self.assertEqual(call_args[0][0], self.mock_master.target_system)
        self.assertEqual(call_args[0][1], self.mock_master.target_component)
    
    def test_take_photo_disconnected(self):
        """Test photo capture when disconnected."""
        self.mock_connection.is_connected.return_value = False
        
        with self.assertRaises(ConnectionError):
            self.camera.take_photo()
    
    def test_start_video_success(self):
        """Test successful video start."""
        self.camera.start_video()
        
        # Verify recording state updated
        self.assertTrue(self.camera._is_recording)
        
        # Verify MAVLink command was sent
        self.mock_master.mav.command_long_send.assert_called_once()
    
    def test_stop_video_success(self):
        """Test successful video stop."""
        self.camera._is_recording = True
        self.camera.stop_video()
        
        # Verify recording state updated
        self.assertFalse(self.camera._is_recording)
        
        # Verify MAVLink command was sent
        self.mock_master.mav.command_long_send.assert_called_once()
    
    def test_video_already_recording(self):
        """Test starting video when already recording."""
        self.camera._is_recording = True
        
        result = self.camera.start_video()
        
        # Should return True but not send command
        self.assertTrue(result)
        self.mock_master.mav.command_long_send.assert_not_called()
    
    def test_stop_video_not_recording(self):
        """Test stopping video when not recording."""
        result = self.camera.stop_video()
        
        # Should return True but not send command
        self.assertTrue(result)
        self.mock_master.mav.command_long_send.assert_not_called()
    
    def test_set_camera_mode_valid(self):
        """Test setting valid camera mode."""
        result = self.camera.set_camera_mode("VIDEO")
        
        self.assertTrue(result)
        self.assertEqual(self.camera._camera_mode, "VIDEO")
    
    def test_set_camera_mode_invalid(self):
        """Test setting invalid camera mode."""
        result = self.camera.set_camera_mode("INVALID")
        
        self.assertFalse(result)
        self.assertEqual(self.camera._camera_mode, "PHOTO")
    
    def test_get_camera_status(self):
        """Test getting camera status."""
        status = self.camera.get_camera_status()
        
        self.assertIn("mode", status)
        self.assertIn("is_recording", status)
        self.assertIn("last_photo_time", status)
        self.assertIn("last_video_start_time", status)
    
    def test_is_recording(self):
        """Test is_recording method."""
        self.camera._is_recording = True
        self.assertTrue(self.camera.is_recording())
        
        self.camera._is_recording = False
        self.assertFalse(self.camera.is_recording())
    
    def test_get_camera_mode(self):
        """Test get_camera_mode method."""
        self.camera._camera_mode = "VIDEO"
        self.assertEqual(self.camera.get_camera_mode(), "VIDEO")
    
    def test_time_lapse_photo(self):
        """Test time-lapse photography."""
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = self.camera.time_lapse_photo(interval=0.1, count=3)
        
        self.assertTrue(result)
        # Should have called take_photo 3 times
        self.assertEqual(self.mock_master.mav.command_long_send.call_count, 3)
    
    def test_camera_string_representation(self):
        """Test camera __repr__ method."""
        repr_str = repr(self.camera)
        
        self.assertIn("Camera", repr_str)
        self.assertIn("mode", repr_str)
        self.assertIn("recording", repr_str)


if __name__ == '__main__':
    unittest.main()
