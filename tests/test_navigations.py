"""
test_navigations.py
Tests navigation through the Drone interface.
"""
from drone.drone import Drone

drone = Drone()
try:
    drone.Start()
    drone.navigation.add_waypoint(47.397742, 8.545594, 20, hold_time=5)
    drone.navigation.add_waypoint(47.398000, 8.545800, 25)
    drone.navigation.execute_mission()
finally:
    drone.shutdown()