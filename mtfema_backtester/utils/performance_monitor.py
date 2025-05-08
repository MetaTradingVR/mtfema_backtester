"""
Performance monitoring system for MT 9 EMA Backtester.

This module provides tools for tracking strategy metrics and execution 
performance to identify bottlenecks and improve strategy performance.
"""

import time
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import statistics
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Performance monitoring system that tracks strategy metrics and execution timing.
    
    Features:
    - Real-time performance tracking
    - Operation timing with statistics
    - Strategy event logging
    - Performance report generation
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern for global performance monitor access."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(PerformanceMonitor, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, enabled: bool = True, report_dir: Optional[str] = None):
        """
        Initialize the performance monitor.
        
        Args:
            enabled: Whether performance monitoring is enabled
            report_dir: Directory to save performance reports
        """
        # Skip re-initialization if already initialized
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        self.enabled = enabled
        self.report_dir = report_dir or os.path.join(os.getcwd(), 'reports', 'performance')
        
        # Create report directory if it doesn't exist
        if self.enabled and not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir, exist_ok=True)
        
        # Strategy metrics
        self.strategy_metrics = defaultdict(int)
        
        # Initialize standard strategy metrics
        self.strategy_metrics.update({
            'extensions_detected': 0,
            'reclamations_detected': 0,
            'valid_pullbacks': 0,
            'paperfeet_transitions': 0,
            'signals_generated': 0,
            'signals_executed': 0,
            'timeframe_conflicts': 0,
            'positions_opened': 0,
            'positions_closed': 0,
            'stops_triggered': 0,
            'targets_hit': 0,
            'failed_entries': 0
        })
        
        # Execution timing metrics
        self.timing_metrics = defaultdict(list)
        
        # Current operation timers
        self.active_timers = {}
        
        # Strategy events log
        self.events = []
        
        # Timestamp when monitoring started
        self.start_time = datetime.now()
        
        logger.info("Performance monitoring initialized")
    
    def start_timer(self, operation: str) -> None:
        """
        Start timing an operation.
        
        Args:
            operation: Name of the operation to time
        """
        if not self.enabled:
            return
            
        self.active_timers[operation] = time.time()
    
    def end_timer(self, operation: str) -> Optional[float]:
        """
        End timing an operation and record its duration.
        
        Args:
            operation: Name of the operation to time
            
        Returns:
            Duration of the operation in milliseconds, or None if timer not started
        """
        if not self.enabled or operation not in self.active_timers:
            return None
            
        start_time = self.active_timers.pop(operation)
        duration_ms = (time.time() - start_time) * 1000
        
        # Record duration
        self.timing_metrics[operation].append(duration_ms)
        
        return duration_ms
    
    def increment_metric(self, metric: str, amount: int = 1) -> None:
        """
        Increment a strategy metric counter.
        
        Args:
            metric: Name of the metric to increment
            amount: Amount to increment by (default: 1)
        """
        if not self.enabled:
            return
            
        self.strategy_metrics[metric] += amount
    
    def set_metric(self, metric: str, value: int) -> None:
        """
        Set a strategy metric to a specific value.
        
        Args:
            metric: Name of the metric
            value: Value to set
        """
        if not self.enabled:
            return
            
        self.strategy_metrics[metric] = value
    
    def log_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """
        Log a strategy event with detailed information.
        
        Args:
            event_type: Type of event (e.g., "SIGNAL", "CONFLICT", "TRADE")
            details: Dictionary with event details
        """
        if not self.enabled:
            return
            
        # Add timestamp to event
        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            **details
        }
        
        self.events.append(event)
    
    def get_timing_stats(self, operation: Optional[str] = None) -> Dict[str, Dict[str, float]]:
        """
        Get timing statistics for operations.
        
        Args:
            operation: Optional operation name to get stats for, or None for all
            
        Returns:
            Dictionary of timing statistics by operation
        """
        if not self.enabled:
            return {}
            
        stats = {}
        
        # Filter operations if specified
        operations = [operation] if operation else self.timing_metrics.keys()
        
        for op in operations:
            if op not in self.timing_metrics or not self.timing_metrics[op]:
                continue
                
            durations = self.timing_metrics[op]
            
            stats[op] = {
                "count": len(durations),
                "min_ms": min(durations),
                "max_ms": max(durations),
                "avg_ms": statistics.mean(durations),
                "median_ms": statistics.median(durations),
                "total_ms": sum(durations)
            }
            
            # Add standard deviation if we have enough samples
            if len(durations) > 1:
                stats[op]["std_dev_ms"] = statistics.stdev(durations)
            
        return stats
    
    def get_metrics(self) -> Dict[str, int]:
        """
        Get all strategy metrics.
        
        Returns:
            Dictionary of metric names and values
        """
        if not self.enabled:
            return {}
            
        return dict(self.strategy_metrics)
    
    def get_events(self, event_type: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get strategy events, optionally filtered by type.
        
        Args:
            event_type: Optional event type to filter by
            limit: Maximum number of events to return (most recent first)
            
        Returns:
            List of event dictionaries
        """
        if not self.enabled:
            return []
            
        # Filter events by type if specified
        filtered_events = self.events
        if event_type:
            filtered_events = [e for e in self.events if e["type"] == event_type]
        
        # Sort by timestamp (most recent first)
        sorted_events = sorted(filtered_events, key=lambda e: e["timestamp"], reverse=True)
        
        # Apply limit if specified
        if limit is not None:
            sorted_events = sorted_events[:limit]
            
        return sorted_events
    
    def generate_report(self, report_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report.
        
        Args:
            report_name: Optional name for the report file
            
        Returns:
            Dictionary with the complete performance report
        """
        if not self.enabled:
            return {}
            
        # Generate report data
        report = {
            "generated_at": datetime.now().isoformat(),
            "monitoring_duration": (datetime.now() - self.start_time).total_seconds(),
            "strategy_metrics": self.get_metrics(),
            "timing_stats": self.get_timing_stats(),
            "event_counts": self._count_events_by_type(),
            "events_sample": self.get_events(limit=100)  # Include last 100 events
        }
        
        # Save report to file if report_name provided
        if report_name:
            file_name = report_name if report_name.endswith('.json') else f"{report_name}.json"
            file_path = os.path.join(self.report_dir, file_name)
            
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2)
                
            logger.info(f"Performance report saved to {file_path}")
        
        return report
    
    def _count_events_by_type(self) -> Dict[str, int]:
        """
        Count events by type.
        
        Returns:
            Dictionary of event types and counts
        """
        counts = defaultdict(int)
        
        for event in self.events:
            counts[event["type"]] += 1
            
        return dict(counts)
    
    def reset(self) -> None:
        """
        Reset all metrics, timers, and events.
        """
        if not self.enabled:
            return
            
        # Reset strategy metrics
        for key in self.strategy_metrics:
            self.strategy_metrics[key] = 0
            
        # Reset timing metrics
        self.timing_metrics.clear()
        
        # Reset active timers
        self.active_timers.clear()
        
        # Reset events
        self.events.clear()
        
        # Reset start time
        self.start_time = datetime.now()
        
        logger.info("Performance monitor reset")

    def summary_report(self) -> str:
        """
        Generate a human-readable summary of performance metrics.
        
        Returns:
            String with formatted performance summary
        """
        if not self.enabled:
            return "Performance monitoring disabled"
            
        # Generate timing stats 
        timing_stats = self.get_timing_stats()
        
        # Format the report
        lines = []
        lines.append("=" * 60)
        lines.append("PERFORMANCE MONITORING SUMMARY")
        lines.append("=" * 60)
        lines.append(f"Duration: {(datetime.now() - self.start_time).total_seconds():.2f} seconds")
        lines.append("")
        
        # Strategy metrics
        lines.append("STRATEGY METRICS")
        lines.append("-" * 60)
        for metric, value in sorted(self.get_metrics().items()):
            lines.append(f"{metric+':':<30} {value}")
        lines.append("")
        
        # Timing statistics
        lines.append("TIMING STATISTICS")
        lines.append("-" * 60)
        lines.append(f"{'Operation':<30} {'Count':>8} {'Avg (ms)':>10} {'Med (ms)':>10} {'Max (ms)':>10}")
        lines.append("-" * 60)
        
        for op, stats in sorted(timing_stats.items()):
            lines.append(f"{op:<30} {stats['count']:>8} {stats['avg_ms']:>10.2f} {stats['median_ms']:>10.2f} {stats['max_ms']:>10.2f}")
        lines.append("")
        
        # Event counts
        event_counts = self._count_events_by_type()
        if event_counts:
            lines.append("EVENT COUNTS")
            lines.append("-" * 60)
            for event_type, count in sorted(event_counts.items()):
                lines.append(f"{event_type+':':<30} {count}")
        
        return "\n".join(lines)


# Context manager for timing operations
class TimingContext:
    """
    Context manager for timing operations.
    
    Example:
        ```
        with TimingContext("data_loading"):
            # Code to time
            load_data()
        ```
    """
    
    def __init__(self, operation: str):
        """
        Initialize the timing context.
        
        Args:
            operation: Name of the operation to time
        """
        self.operation = operation
        self.monitor = get_performance_monitor()
    
    def __enter__(self):
        """Start the timer when entering the context."""
        self.monitor.start_timer(self.operation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """End the timer when exiting the context."""
        duration = self.monitor.end_timer(self.operation)
        if exc_type is not None:
            logger.warning(f"Operation {self.operation} failed after {duration:.2f}ms: {exc_val}")


# Decorator for timing functions
def time_operation(func):
    """
    Decorator for timing function execution.
    
    Example:
        ```
        @time_operation
        def process_data(data):
            # Function code
            pass
        ```
    """
    def wrapper(*args, **kwargs):
        monitor = get_performance_monitor()
        operation = func.__name__
        
        monitor.start_timer(operation)
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            monitor.end_timer(operation)
    
    return wrapper


# Helper functions for easier access

def get_performance_monitor() -> PerformanceMonitor:
    """
    Get the global performance monitor instance.
    
    Returns:
        PerformanceMonitor instance
    """
    return PerformanceMonitor()

def log_strategy_event(event_type: str, **details) -> None:
    """
    Log a strategy event with the global performance monitor.
    
    Args:
        event_type: Type of event
        **details: Event details as keyword arguments
    """
    monitor = get_performance_monitor()
    monitor.log_event(event_type, details)

def increment_strategy_metric(metric: str, amount: int = 1) -> None:
    """
    Increment a strategy metric with the global performance monitor.
    
    Args:
        metric: Name of the metric
        amount: Amount to increment by (default: 1)
    """
    monitor = get_performance_monitor()
    monitor.increment_metric(metric, amount)
