"""
follow_me.py
Provides follow-me mode for tracking moving targets.
The drone follows a target based on GPS coordinates with configurable distance and altitude.
Author: Emmanuel Ugwu
Project: DroneNEA
"""

import logging
import time
import threading
import math
from typing import Optional, Callable
from drone.navigations import Waypoint, Navigation
from drone.telemetry import Telemetry
from drone.config import config

logger = logging.getLogger(__name__)


class FollowMeMode:
    """
    Follow-me mode for tracking moving targets.
    The drone maintains a specified distance and altitude from a moving target.
    """
    
    def __init__(self, navigation: Navigation, telemetry: Telemetry):
        """
        Initialize follow-me mode.
        
        Parameters:
            navigation: Navigation - Navigation system instance
            telemetry: Telemetry - Telemetry system instance
        """
        self.navigation = navigation
        self.telemetry = telemetry
        self.running = False
        self.target_position = None  # (lat, lon, alt)
        self.follow_distance = 10  # meters
        self.follow_altitude = 20  # meters
        self.update_interval = 1.0  # seconds
        self.acceptance_radius = 5  # meters
        self._follow_thread = None
        self._stop_event = threading.Event()
        
    def start_following(
        self,
        initial_lat: float,
        initial_lon: float,
        altitude: float = 20,
        follow_distance: float = 10,
        update_interval: float = 1.0
    ) -> bool:
        """
        Start follow-me mode with initial target position.
        
        Parameters:
            initial_lat: float - Initial target latitude
            initial_lon: float - Initial target longitude
            altitude: float - Follow altitude in meters
            follow_distance: float - Distance to maintain from target in meters
            update_interval: float - Position update interval in seconds
            
        Returns:
            bool - True if follow-me mode started successfully
        """
        # TODO: Implement this method
        # Steps:
        # 1. Validate parameters
        # 2. Set target position
        # 3. Configure follow parameters
        # 4. Start background thread for tracking
        # 5. Return success/failure
        
        logger.info("Follow-me mode started (TO BE IMPLEMENTED)")
        return True
    
    def update_target_position(self, lat: float, lon: float, alt: Optional[float] = None):
        """
        Update the target's current position.
        
        Parameters:
            lat: float - Target latitude
            lon: float - Target longitude
            alt: Optional[float] - Target altitude (optional, uses follow_altitude if not provided)
        """
        # TODO: Implement this method
        # Steps:
        # 1. Update target_position with new coordinates
        # 2. Log the update
        # 3. The background thread will use this to update drone position
        
        logger.info(f"Target position updated: {lat}, {lon}")
    
    def stop_following(self):
        """
        Stop follow-me mode and hold current position.
        """
        # TODO: Implement this method
        # Steps:
        # 1. Set running flag to False
        # 2. Signal stop event
        # 3. Wait for thread to join
        # 4. Hold current position
        
        logger.info("Follow-me mode stopped (TO BE IMPLEMENTED)")
    
    def _follow_loop(self):
        """
        Background thread loop for continuous target tracking.
        This runs in a separate thread to continuously update drone position.
        """
        # TODO: Implement this method
        # Steps:
        # 1. While running and not stopped:
        # 2. Get current drone position
        # 3. Calculate distance to target
        # 4. If distance > acceptance_radius, move toward target
        # 5. Wait for update_interval
        # 6. Handle exceptions and log errors
        
        logger.info("Follow loop running (TO BE IMPLEMENTED)")
    
    def _calculate_follow_position(self, target_lat: float, target_lon: float) -> tuple:
        """
        Calculate the position the drone should fly to maintain follow distance.
        
        Parameters:
            target_lat: float - Target latitude
            target_lon: float - Target longitude
            
        Returns:
            tuple - (latitude, longitude) for drone position
        """
        # TODO: Implement this method
        # Steps:
        # 1. Get current drone position
        # 2. Calculate vector from drone to target
        # 3. Normalize the vector
        # 4. Scale by follow_distance
        # 5. Calculate offset position
        # 6. Return the follow position
        
        return (target_lat, target_lon)
    
    def get_status(self) -> dict:
        """
        Get current follow-me mode status.
        
        Returns:
            dict - Status information including running state, target position, etc.
        """
        return {
            'running': self.running,
            'target_position': self.target_position,
            'follow_distance': self.follow_distance,
            'follow_altitude': self.follow_altitude,
            'update_interval': self.update_interval
        }


# Standalone test
if __name__ == "__main__":
    # TODO: Add test code here
    print("Follow-me mode module - Test your implementation here!")
