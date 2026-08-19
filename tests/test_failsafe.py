"""
Test suite for failsafe.py module.
Tests failsafe monitoring and response functionality.
"""

import unittest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
from drone.failsafe import Failsafe, FailsafeLevel
from drone.connection import Connection
from drone.control import Control
from drone.telemetry import Telemetry


class TestFailsafe(unittest.TestCase):
    """Test cases for Failsafe class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_connection = Mock(spec=Connection)
        self.mock_connection.is_connected.return_value = True
        self.mock_master = Mock()
        self.mock_connection.get_master.return_value = self.mock_master
        
        self.mock_control = Mock(spec=Control)
        self.mock_telemetry = Mock(spec=Telemetry)
        
        self.failsafe = Failsafe(self.mock_connection, self.mock_control, self.mock_telemetry)
    
    def test_failsafe_initialization(self):
        """Test failsafe initialization."""
        self.assertIsNotNone(self.failsafe.connection)
        self.assertIsNotNone(self.failsafe.control)
        self.assertIsNotNone(self.failsafe.telemetry)
        self.assertFalse(self.failsafe._monitoring_active)
        self.assertIsNone(self.failsafe._current_failsafe_level)
    
    def test_check_battery_warning(self):
        """Test battery check at warning level."""
        self.mock_telemetry.get_battery.return_value = 20  # Below warning threshold
        
        result = self.failsafe._check_battery()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], FailsafeLevel.WARNING)
        self.assertIn("battery", result[1].lower())
    
    def test_check_battery_critical(self):
        """Test battery check at critical level."""
        self.mock_telemetry.get_battery.return_value = 12  # Below critical threshold
        
        result = self.failsafe._check_battery()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], FailsafeLevel.CRITICAL)
        self.assertIn("battery", result[1].lower())
    
    def test_check_battery_emergency(self):
        """Test battery check at emergency level."""
        self.mock_telemetry.get_battery.return_value = 8  # Below emergency threshold
        
        result = self.failsafe._check_battery()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], FailsafeLevel.EMERGENCY)
        self.assertIn("battery", result[1].lower())
    
    def test_check_battery_normal(self):
        """Test battery check with normal level."""
        self.mock_telemetry.get_battery.return_value = 50  # Normal level
        
        result = self.failsafe._check_battery()
        
        self.assertIsNone(result)
    
    def test_check_battery_unavailable(self):
        """Test battery check when data unavailable."""
        self.mock_telemetry.get_battery.return_value = None
        
        result = self.failsafe._check_battery()
        
        self.assertIsNone(result)
    
    def test_check_link_timeout(self):
        """Test link check with heartbeat timeout."""
        # Simulate heartbeat timeout
        self.failsafe._last_heartbeat_time = time.time() - 100  # 100 seconds ago
        
        result = self.failsafe._check_link()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], FailsafeLevel.EMERGENCY)
        self.assertIn("heartbeat", result[1].lower())
    
    def test_check_link_normal(self):
        """Test link check with normal heartbeat."""
        # Recent heartbeat
        self.failsafe._last_heartbeat_time = time.time() - 1  # 1 second ago
        
        result = self.failsafe._check_link()
        
        self.assertIsNone(result)
    
    def test_check_gps_insufficient_satellites(self):
        """Test GPS check with insufficient satellites."""
        self.mock_telemetry.get_gps.return_value = {
            "satellites": 4,  # Below minimum
            "fix_type": 3
        }
        
        result = self.failsafe.check_gps()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], FailsafeLevel.CRITICAL)
        self.assertIn("satellites", result[1].lower())
    
    def test_check_gps_invalid_fix(self):
        """Test GPS check with invalid fix type."""
        self.mock_telemetry.get_gps.return_value = {
            "satellites": 8,
            "fix_type": 1  # Invalid fix type
        }
        
        result = self.failsafe.check_gps()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], FailsafeLevel.CRITICAL)
        self.assertIn("fix", result[1].lower())
    
    def test_check_gps_normal(self):
        """Test GPS check with normal parameters."""
        self.mock_telemetry.get_gps.return_value = {
            "satellites": 10,
            "fix_type": 3
        }
        
        result = self.failsafe.check_gps()
        
        self.assertIsNone(result)
    
    def test_check_gps_unavailable(self):
        """Test GPS check when data unavailable."""
        self.mock_telemetry.get_gps.return_value = None
        
        result = self.failsafe.check_gps()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], FailsafeLevel.CRITICAL)
    
    def test_check_altitude_critical(self):
        """Test altitude check at critical level."""
        self.mock_telemetry.get_altitude.return_value = 125  # Above critical threshold
        
        result = self.failsafe.check_altitude()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], FailsafeLevel.CRITICAL)
        self.assertIn("altitude", result[1].lower())
    
    def test_check_altitude_warning(self):
        """Test altitude check at warning level."""
        self.mock_telemetry.get_altitude.return_value = 105  # Above warning threshold
        
        result = self.failsafe.check_altitude()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], FailsafeLevel.WARNING)
    
    def test_check_altitude_normal(self):
        """Test altitude check with normal altitude."""
        self.mock_telemetry.get_altitude.return_value = 50  # Normal altitude
        
        result = self.failsafe.check_altitude()
        
        self.assertIsNone(result)
    
    def test_check_all(self):
        """Test running all on-demand checks."""
        self.mock_telemetry.get_battery.return_value = 50
        self.mock_telemetry.get_gps.return_value = {"satellites": 10, "fix_type": 3}
        self.mock_telemetry.get_altitude.return_value = 50
        
        results = self.failsafe.check_all()
        
        self.assertIn("gps", results)
        self.assertIn("altitude", results)
        self.assertIn("battery", results)
        self.assertIn("link", results)
        self.assertIn("timestamp", results)
    
    def test_trigger_failsafe_manual(self):
        """Test manual failsafe trigger."""
        self.failsafe.trigger_failsafe(FailsafeLevel.WARNING, "Test trigger")
        
        self.assertEqual(self.failsafe._current_failsafe_level, FailsafeLevel.WARNING)
        self.assertEqual(self.failsafe._failsafe_reason, "Test trigger")
        self.assertEqual(self.failsafe._failsafe_count, 1)
    
    def test_set_callbacks(self):
        """Test setting failsafe callbacks."""
        mock_caution = Mock()
        mock_critical = Mock()
        mock_emergency = Mock()
        
        self.failsafe.set_callbacks(
            on_caution=mock_caution,
            on_critical=mock_critical,
            on_emergency=mock_emergency
        )
        
        self.assertEqual(self.failsafe._on_caution, mock_caution)
        self.assertEqual(self.failsafe._on_critical, mock_critical)
        self.assertEqual(self.failsafe._on_emergency, mock_emergency)
    
    def test_get_status(self):
        """Test getting failsafe status."""
        status = self.failsafe.get_status()
        
        self.assertIn("monitoring_active", status)
        self.assertIn("current_level", status)
        self.assertIn("current_reason", status)
        self.assertIn("failsafe_count", status)
        self.assertIn("last_heartbeat", status)
    
    def test_reset_failsafe(self):
        """Test resetting failsafe state."""
        self.failsafe._current_failsafe_level = FailsafeLevel.CRITICAL
        self.failsafe._failsafe_reason = "Test"
        
        self.failsafe.reset_failsafe()
        
        self.assertIsNone(self.failsafe._current_failsafe_level)
        self.assertIsNone(self.failsafe._failsafe_reason)
    
    def test_is_monitoring(self):
        """Test monitoring status check."""
        self.assertFalse(self.failsafe.is_monitoring())
        
        self.failsafe._monitoring_active = True
        self.assertTrue(self.failsafe.is_monitoring())
    
    def test_start_monitoring(self):
        """Test starting background monitoring."""
        self.failsafe.start_monitoring()
        
        self.assertTrue(self.failsafe._monitoring_active)
        self.assertIsNotNone(self.failsafe._monitor_thread)
        
        # Clean up
        self.failsafe.stop_monitoring()
    
    def test_stop_monitoring(self):
        """Test stopping background monitoring."""
        self.failsafe.start_monitoring()
        self.failsafe.stop_monitoring()
        
        self.assertFalse(self.failsafe._monitoring_active)
    
    def test_failsafe_string_representation(self):
        """Test failsafe __repr__ method."""
        repr_str = repr(self.failsafe)
        
        self.assertIn("Failsafe", repr_str)
        self.assertIn("monitoring", repr_str)
        self.assertIn("level", repr_str)
        self.assertIn("count", repr_str)


if __name__ == '__main__':
    unittest.main()
