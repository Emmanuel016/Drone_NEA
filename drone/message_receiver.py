"""
message_receiver.py
Central MAVLink message receiver and distributor.
Implements a publish-subscribe pattern for efficient message distribution
to all drone subsystems.
Author: Emmanuel Ugwu
Project: DroneNEA
"""

import logging
import threading
import time
from typing import Dict, List, Callable, Optional, Any, Set
from collections import defaultdict
from drone.connection import Connection
from drone.config import config
from drone.exceptions import ConnectionError as DroneConnectionError

# Configure module-specific logger
logger = logging.getLogger(__name__)


class MessageReceiver:
    """
    Central MAVLink message receiver and distributor.
    This class runs a single message listener loop that receives all MAVLink
    messages and distributes them to registered subscribers based on message
    type. This eliminates message contention between modules and provides
    a clean separation of concerns.
    
    Architecture:
        MAVLink Connection -> Message Receiver -> Subscribers (Telemetry, Camera, Failsafe, etc.)
    
    Features:
        - Single message listener loop
        - Publish-subscribe pattern for message distribution
        - Thread-safe message handling
        - Message caching for latest values
        - Callback-based subscriber notifications
    """
    
    def __init__(self, connection: Connection):
        """
        Initialize the central message receiver.
        Parameters:
            connection: Active MAVLink connection
        """
        self.connection = connection
        self.master = connection.get_master()
        
        # Subscriber management
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self._subscribers_lock = threading.Lock()
        
        # Message cache (latest message of each type)
        self._message_cache: Dict[str, Any] = {}
        self._cache_lock = threading.Lock()
        
        # Receiver thread management
        self._receiver_running = False
        self._receiver_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Statistics
        self._message_count = 0
        self._stats_lock = threading.Lock()
        
        logger.info("Message receiver initialized")
    
    def _check_connection(self):
        """Ensure the vehicle is connected."""
        if not self.connection.is_connected():
            raise DroneConnectionError("Drone is not connected.")
    
    def subscribe(self, message_type: str, callback: Callable):
        """
        Subscribe to a specific MAVLink message type.
        Parameters:
            message_type: str - MAVLink message type (e.g., 'GLOBAL_POSITION_INT', 'HEARTBEAT')
            callback: Callable - Function to call when message is received
                            Signature: callback(message) -> None
        """
        with self._subscribers_lock:
            self._subscribers[message_type].append(callback)
        logger.debug(f"Subscribed to {message_type}: {callback.__name__}")
    
    def unsubscribe(self, message_type: str, callback: Callable):
        """
        Unsubscribe from a specific MAVLink message type.
        Parameters:
            message_type: str - MAVLink message type
            callback: Callable - Callback function to remove
        """
        with self._subscribers_lock:
            if callback in self._subscribers[message_type]:
                self._subscribers[message_type].remove(callback)
                logger.debug(f"Unsubscribed from {message_type}: {callback.__name__}")
    
    def subscribe_all(self, callback: Callable):
        """
        Subscribe to all MAVLink message types.
        
        Parameters:
            callback: Callable - Function to call for any message
        """
        with self._subscribers_lock:
            self._subscribers['*'].append(callback)
        logger.debug(f"Subscribed to all messages: {callback.__name__}")
    
    def unsubscribe_all(self, callback: Callable):
        """
        Unsubscribe from all message types.
        Parameters:
            callback: Callable - Callback function to remove
        """
        with self._subscribers_lock:
            if callback in self._subscribers['*']:
                self._subscribers['*'].remove(callback)
            # Also remove from specific message types
            for msg_type in list(self._subscribers.keys()):
                if msg_type != '*' and callback in self._subscribers[msg_type]:
                    self._subscribers[msg_type].remove(callback)
        logger.debug(f"Unsubscribed from all messages: {callback.__name__}")
    
    def get_cached_message(self, message_type: str) -> Optional[Any]:
        """
        Get the latest cached message of a specific type.
        Parameters:
            message_type: str - MAVLink message type
        Returns:
            Latest message of the type, or None if not available
        """
        with self._cache_lock:
            return self._message_cache.get(message_type)
    
    def get_all_cached_messages(self) -> Dict[str, Any]:
        """
        Get all cached messages.
        Returns:
            Dict of all cached messages by type
        """
        with self._cache_lock:
            return self._message_cache.copy()
    
    def start(self):
        """Start the message receiver thread."""
        if self._receiver_running:
            logger.warning("Message receiver already running")
            return
        
        self._check_connection()
        self._receiver_running = True
        self._stop_event.clear()
        self._receiver_thread = threading.Thread(
            target=self._receiver_loop,
            daemon=True,
            name="MessageReceiver"
        )
        self._receiver_thread.start()
        logger.info("Message receiver started")
    
    def stop(self):
        """Stop the message receiver thread."""
        if not self._receiver_running:
            logger.warning("Message receiver not running")
            return
        
        self._receiver_running = False
        self._stop_event.set()
        
        if self._receiver_thread:
            self._receiver_thread.join(timeout=5)
            if self._receiver_thread.is_alive():
                logger.warning("Message receiver did not stop gracefully")
            else:
                logger.info("Message receiver stopped gracefully")
    
    def _receiver_loop(self):
        """Main message receiver loop."""
        logger.info("Message receiver loop started")
        
        while not self._stop_event.is_set() and self.connection.is_connected():
            try:
                # Receive any message with timeout
                msg = self.master.recv_match(timeout=1.0)
                if msg:
                    self._process_message(msg)
            except Exception as e:
                logger.error(f"Error in message receiver loop: {e}")
                time.sleep(0.1)
        logger.info("Message receiver loop ended")
    
    def _process_message(self, msg):
        """
        Process a received message and distribute to subscribers.
        
        Parameters:
            msg: MAVLink message
        """
        msg_type = msg.get_type()
        
        # Update statistics
        with self._stats_lock:
            self._message_count += 1
        
        # Cache the message
        with self._cache_lock:
            self._message_cache[msg_type] = msg
        
        # Get subscribers for this message type
        with self._subscribers_lock:
            subscribers = []
            # Add type-specific subscribers
            if msg_type in self._subscribers:
                subscribers.extend(self._subscribers[msg_type])
            # Add universal subscribers (subscribed to all messages)
            if '*' in self._subscribers:
                subscribers.extend(self._subscribers['*'])
        
        # Distribute message to subscribers
        for callback in subscribers:
            try:
                callback(msg)
            except Exception as e:
                logger.error(f"Error in subscriber callback {callback.__name__}: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get receiver statistics.
        Returns:
            Dict with statistics information
        """
        with self._stats_lock:
            message_count = self._message_count
        with self._subscribers_lock:
            subscriber_count = sum(len(subs) for subs in self._subscribers.values())
            message_types = list(self._subscribers.keys())
        with self._cache_lock:
            cached_types = list(self._message_cache.keys())
        return {
            "running": self._receiver_running,
            "message_count": message_count,
            "subscriber_count": subscriber_count,
            "subscribed_message_types": message_types,
            "cached_message_types": cached_types
        }
    
    def is_running(self) -> bool:
        """Check if the receiver is running."""
        return self._receiver_running
    
    def __repr__(self) -> str:
        return (f"MessageReceiver("
                f"running={self._receiver_running}, "
                f"subscribers={len(self._subscribers)}, "
                f"cached={len(self._message_cache)})")


# Standalone test
if __name__ == "__main__":
    from drone.connection import Connection
    
    # Test message receiver
    connection = Connection()
    
    try:
        connection.connect()
        receiver = MessageReceiver(connection)
        
        # Define test subscribers
        def heartbeat_subscriber(msg):
            print(f"Heartbeat: System={msg.system_status}, Type={msg.type}")
        
        def position_subscriber(msg):
            print(f"Position: Alt={msg.relative_alt/1000:.2f}m")
        
        def all_subscriber(msg):
            print(f"All messages: {msg.get_type()}")
        
        # Subscribe to messages
        receiver.subscribe('HEARTBEAT', heartbeat_subscriber)
        receiver.subscribe('GLOBAL_POSITION_INT', position_subscriber)
        receiver.subscribe_all(all_subscriber)
        
        # Start receiver
        receiver.start()
        
        print("Message receiver running for 10 seconds...")
        time.sleep(10)
        
        # Print statistics
        print("\nStatistics:")
        print(receiver.get_statistics())
        
        # Print cached messages
        print("\nCached messages:")
        for msg_type, msg in receiver.get_all_cached_messages().items():
            print(f"  {msg_type}: {msg}")
        
        # Stop receiver
        receiver.stop()
        
    except ConnectionError as e:
        logger.error(e)
    finally:
        if connection.is_connected():
            connection.disconnect()
