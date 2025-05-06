"""
Metrics Collection for MT 9 EMA Backtester.

This module provides functionality for collecting anonymous usage metrics
to understand feature usage patterns and improve the application.
"""

import os
import json
import uuid
import time
import logging
import threading
import hashlib
from enum import Enum
from typing import Dict, Any, List, Optional, Set, Callable
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path

# Setup logger
logger = logging.getLogger(__name__)

class MetricCategory(Enum):
    """Categories for metrics to organize data collection."""
    PERFORMANCE = "performance"
    FEATURE_USAGE = "feature_usage"
    USER_ENGAGEMENT = "user_engagement"
    ERROR = "error"
    STRATEGY = "strategy"
    BACKTEST = "backtest"
    COMMUNITY = "community"
    SYSTEM = "system"


@dataclass
class MetricEvent:
    """Represents a single metric event with metadata."""
    
    # Unique identifier for the event
    event_id: str
    
    # Category of the metric
    category: MetricCategory
    
    # Name of the event (e.g., "feature_activated", "backtest_completed")
    name: str
    
    # Additional properties for the event
    properties: Dict[str, Any]
    
    # Timestamp when the event occurred
    timestamp: float
    
    # Anonymous user identifier (hashed)
    user_id: Optional[str] = None
    
    # Session identifier
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "category": self.category.value,
            "name": self.name,
            "properties": self.properties,
            "timestamp": self.timestamp,
            "user_id": self.user_id,
            "session_id": self.session_id
        }


class MetricsCollector:
    """Collects and manages anonymous usage metrics."""
    
    # Singleton instance
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MetricsCollector, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the metrics collector.
        
        Args:
            storage_dir: Directory for storing metrics data
        """
        # Only initialize once (singleton pattern)
        if self._initialized:
            return
            
        self._initialized = True
        
        # Determine storage directory
        self._storage_dir = storage_dir or os.path.join(
            os.path.expanduser("~"), 
            ".mtfema", 
            "metrics"
        )
        
        # Ensure storage directory exists
        os.makedirs(self._storage_dir, exist_ok=True)
        
        # Initialize events queue and lock
        self._events: List[MetricEvent] = []
        self._lock = threading.RLock()
        
        # Generate session ID
        self._session_id = str(uuid.uuid4())
        
        # Opt-out status
        self._is_opted_out = self._load_opt_out_status()
        
        # Setup automatic flushing of events
        self._setup_auto_flush()
        
        logger.info(f"Metrics collector initialized with session ID: {self._session_id}")
        
        # Log initialization event if not opted out
        if not self._is_opted_out:
            self.track_event(
                category=MetricCategory.SYSTEM,
                name="system_initialized",
                properties={"session_id": self._session_id}
            )
    
    def _load_opt_out_status(self) -> bool:
        """
        Load the opt-out status from configuration.
        
        Returns:
            True if the user has opted out, False otherwise
        """
        # Check environment variable first
        if os.environ.get("MTFEMA_METRICS_OPT_OUT", "").lower() in ("true", "1", "yes"):
            return True
            
        # Check configuration file
        config_path = os.path.join(os.path.dirname(self._storage_dir), "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get("metrics_opt_out", False)
            except Exception as e:
                logger.error(f"Error loading opt-out status: {str(e)}")
                
        return False
    
    def _setup_auto_flush(self) -> None:
        """Setup automatic flushing of events."""
        def flush_periodically():
            while True:
                time.sleep(300)  # Flush every 5 minutes
                self.flush()
        
        # Start the flush thread
        thread = threading.Thread(target=flush_periodically, daemon=True)
        thread.start()
    
    def opt_out(self) -> None:
        """Opt out of metrics collection."""
        with self._lock:
            self._is_opted_out = True
            
            # Save opt-out status
            config_path = os.path.join(os.path.dirname(self._storage_dir), "config.json")
            try:
                config = {}
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                
                config["metrics_opt_out"] = True
                
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
            except Exception as e:
                logger.error(f"Error saving opt-out status: {str(e)}")
            
            # Clear existing events
            self._events = []
            
            logger.info("User opted out of metrics collection")
    
    def opt_in(self) -> None:
        """Opt in to metrics collection."""
        with self._lock:
            self._is_opted_out = False
            
            # Save opt-in status
            config_path = os.path.join(os.path.dirname(self._storage_dir), "config.json")
            try:
                config = {}
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                
                config["metrics_opt_out"] = False
                
                with open(config_path, 'w') as f:
                    json.dump(config, f, indent=2)
            except Exception as e:
                logger.error(f"Error saving opt-in status: {str(e)}")
            
            logger.info("User opted in to metrics collection")
            
            # Track opt-in event
            self.track_event(
                category=MetricCategory.SYSTEM,
                name="metrics_opted_in",
                properties={}
            )
    
    def is_opted_out(self) -> bool:
        """
        Check if the user has opted out of metrics collection.
        
        Returns:
            True if opted out, False otherwise
        """
        return self._is_opted_out
    
    def get_anonymous_user_id(self) -> str:
        """
        Get an anonymous, persistent user ID.
        
        This generates a hashed identifier that's consistent for a user
        but cannot be traced back to their identity.
        
        Returns:
            Hashed anonymous ID
        """
        # Use machine-specific but non-PII information to generate a consistent ID
        machine_info = [
            os.getenv("COMPUTERNAME", ""),
            os.getenv("USERNAME", ""),
            str(uuid.getnode())  # MAC address
        ]
        
        # Hash the information to create an anonymous ID
        hash_input = ":".join(machine_info).encode("utf-8")
        return hashlib.sha256(hash_input).hexdigest()
    
    def track_event(self, 
                  category: MetricCategory, 
                  name: str, 
                  properties: Dict[str, Any] = None) -> None:
        """
        Track a usage metric event.
        
        Args:
            category: Category of the metric
            name: Name of the event
            properties: Additional properties for the event
        """
        if self._is_opted_out:
            return
            
        with self._lock:
            event = MetricEvent(
                event_id=str(uuid.uuid4()),
                category=category,
                name=name,
                properties=properties or {},
                timestamp=time.time(),
                user_id=self.get_anonymous_user_id(),
                session_id=self._session_id
            )
            
            self._events.append(event)
            
            # Auto-flush if we have many events
            if len(self._events) >= 100:
                self.flush()
    
    def flush(self) -> bool:
        """
        Flush collected events to storage.
        
        Returns:
            True if successful, False otherwise
        """
        if self._is_opted_out or not self._events:
            return True
            
        with self._lock:
            events_to_flush = self._events.copy()
            self._events = []
        
        try:
            # Create filename based on timestamp
            filename = f"metrics_{int(time.time())}.json"
            filepath = os.path.join(self._storage_dir, filename)
            
            # Write events to file
            with open(filepath, 'w') as f:
                json.dump(
                    [event.to_dict() for event in events_to_flush],
                    f,
                    indent=2
                )
                
            logger.debug(f"Flushed {len(events_to_flush)} metrics events to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error flushing metrics: {str(e)}")
            
            # Put events back in the queue
            with self._lock:
                self._events = events_to_flush + self._events
                
            return False
    
    def get_events(self) -> List[MetricEvent]:
        """
        Get all events in the current queue.
        
        Returns:
            List of metric events
        """
        with self._lock:
            return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear all events in the current queue."""
        with self._lock:
            self._events = []


# Global instance
metrics_collector = MetricsCollector()

def get_metrics_collector() -> MetricsCollector:
    """
    Get the global metrics collector instance.
    
    Returns:
        MetricsCollector instance
    """
    return metrics_collector

def track_event(category: MetricCategory, name: str, properties: Dict[str, Any] = None) -> None:
    """
    Track a usage metric event.
    
    Args:
        category: Category of the metric
        name: Name of the event
        properties: Additional properties for the event
    """
    metrics_collector.track_event(category, name, properties or {})

def track_feature_usage(feature_name: str, properties: Dict[str, Any] = None) -> None:
    """
    Track feature usage.
    
    Args:
        feature_name: Name of the feature being used
        properties: Additional properties for the event
    """
    props = properties or {}
    props["feature_name"] = feature_name
    
    track_event(
        category=MetricCategory.FEATURE_USAGE,
        name="feature_used",
        properties=props
    )

def track_error(error_type: str, error_message: str, properties: Dict[str, Any] = None) -> None:
    """
    Track an error.
    
    Args:
        error_type: Type of error
        error_message: Error message
        properties: Additional properties for the event
    """
    props = properties or {}
    props.update({
        "error_type": error_type,
        "error_message": error_message
    })
    
    track_event(
        category=MetricCategory.ERROR,
        name="error_occurred",
        properties=props
    )

def track_performance(operation: str, duration_ms: float, properties: Dict[str, Any] = None) -> None:
    """
    Track a performance metric.
    
    Args:
        operation: Operation being measured
        duration_ms: Duration in milliseconds
        properties: Additional properties for the event
    """
    props = properties or {}
    props.update({
        "operation": operation,
        "duration_ms": duration_ms
    })
    
    track_event(
        category=MetricCategory.PERFORMANCE,
        name="performance_metric",
        properties=props
    )

def with_metrics(feature_name: str, include_duration: bool = True):
    """
    Decorator to track feature usage and optionally measure performance.
    
    Args:
        feature_name: Name of the feature being used
        include_duration: Whether to include duration measurement
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Skip if opted out
            if metrics_collector.is_opted_out():
                return func(*args, **kwargs)
            
            start_time = time.time()
            
            try:
                # Execute the function
                result = func(*args, **kwargs)
                
                # Track successful usage
                props = {}
                
                if include_duration:
                    duration_ms = (time.time() - start_time) * 1000
                    props["duration_ms"] = duration_ms
                
                track_feature_usage(feature_name, props)
                
                return result
            except Exception as e:
                # Track error
                track_error(
                    error_type=type(e).__name__,
                    error_message=str(e),
                    properties={"feature_name": feature_name}
                )
                raise
        return wrapper
    return decorator 