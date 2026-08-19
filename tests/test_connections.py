"""
test_connection.py
Tests the Connection class through the Drone interface.
"""

from drone.drone import Drone

def main():
    print("=" * 60)
    print("Testing Drone Connection")
    print("=" * 60)

    drone = Drone()

    try:
        # Startup drone (includes connection)
        if not drone.Start():
            print("\nConnection test FAILED: Startup failed")
            return

        # Check connection state
        print(f"\nConnected: {drone.connection.is_connected()}")

        # Get MAVLink object
        master = drone.connection.get_master()

        print(f"System ID      : {master.target_system}")
        print(f"Component ID   : {master.target_component}")
        print(f"Flight Mode    : {master.flightmode}")

        print("\nConnection test PASSED")

    except Exception as error:
        print(f"\nConnection test FAILED")
        print(error)

    finally:
        drone.shutdown()


if __name__ == "__main__":
    main()
