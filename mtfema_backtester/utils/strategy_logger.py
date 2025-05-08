"""
Structured logging system for MT 9 EMA Strategy.

This module provides a detailed logging system for strategy decisions, 
making it easier to track and debug strategy behavior.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import threading
import pandas as pd

logger = logging.getLogger(__name__)

class StrategyLogger:
    """
    Structured logging system for strategy decisions and events.
    
    Features:
    - Detailed logging of strategy decisions with context
    - Signal tracking from generation to execution
    - Conflict resolution logging
    - Trade management logging
    - Export to various formats for analysis
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern for global strategy logger access."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(StrategyLogger, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, enabled: bool = True, log_dir: Optional[str] = None):
        """
        Initialize the strategy logger.
        
        Args:
            enabled: Whether logging is enabled
            log_dir: Directory to save log files
        """
        # Skip re-initialization if already initialized
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        self.enabled = enabled
        self.log_dir = log_dir or os.path.join(os.getcwd(), 'logs', 'strategy')
        
        # Create log directory if it doesn't exist
        if self.enabled and not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir, exist_ok=True)
        
        # Initialize log storage
        self.signal_logs = []
        self.conflict_logs = []
        self.trade_logs = []
        self.indicator_logs = []
        self.system_logs = []
        
        # Session identifier
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        logger.info(f"Strategy logger initialized with session ID: {self.session_id}")
    
    def log_signal(self, timeframe: str, direction: str, reason: str, **details) -> None:
        """
        Log a trading signal with detailed information.
        
        Args:
            timeframe: Signal timeframe
            direction: Signal direction (LONG/SHORT)
            reason: Reason for the signal
            **details: Additional signal details
        """
        if not self.enabled:
            return
            
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "SIGNAL",
            "timeframe": timeframe,
            "direction": direction,
            "reason": reason,
            **details
        }
        
        self.signal_logs.append(log_entry)
        logger.debug(f"Signal logged: {direction} on {timeframe} - {reason}")
    
    def log_conflict(self, timeframes: List[str], conflict_type: str, resolution: str, **details) -> None:
        """
        Log a timeframe conflict and its resolution.
        
        Args:
            timeframes: List of timeframes involved in the conflict
            conflict_type: Type of conflict
            resolution: How the conflict was resolved
            **details: Additional conflict details
        """
        if not self.enabled:
            return
            
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "CONFLICT",
            "timeframes": timeframes,
            "conflict_type": conflict_type,
            "resolution": resolution,
            **details
        }
        
        self.conflict_logs.append(log_entry)
        logger.debug(f"Conflict logged: {conflict_type} between {timeframes} - {resolution}")
    
    def log_trade(self, action: str, timeframe: str, direction: str, **details) -> None:
        """
        Log a trade action.
        
        Args:
            action: Trade action (ENTRY, EXIT, STOP, TARGET)
            timeframe: Trade timeframe
            direction: Trade direction (LONG/SHORT)
            **details: Additional trade details
        """
        if not self.enabled:
            return
            
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "TRADE",
            "action": action,
            "timeframe": timeframe,
            "direction": direction,
            **details
        }
        
        self.trade_logs.append(log_entry)
        logger.debug(f"Trade logged: {action} {direction} on {timeframe}")
    
    def log_indicator(self, timeframe: str, indicator: str, value: Any, **details) -> None:
        """
        Log an indicator calculation result.
        
        Args:
            timeframe: Indicator timeframe
            indicator: Indicator name
            value: Indicator value
            **details: Additional indicator details
        """
        if not self.enabled:
            return
            
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "INDICATOR",
            "timeframe": timeframe,
            "indicator": indicator,
            "value": value,
            **details
        }
        
        self.indicator_logs.append(log_entry)
    
    def log_system(self, event: str, **details) -> None:
        """
        Log a system event.
        
        Args:
            event: System event description
            **details: Additional event details
        """
        if not self.enabled:
            return
            
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "SYSTEM",
            "event": event,
            **details
        }
        
        self.system_logs.append(log_entry)
        logger.info(f"System event logged: {event}")
    
    def get_signal_logs(self, timeframe: Optional[str] = None, direction: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get signal logs, optionally filtered by timeframe and direction.
        
        Args:
            timeframe: Optional timeframe filter
            direction: Optional direction filter
            
        Returns:
            List of signal log entries
        """
        if not self.enabled:
            return []
            
        filtered_logs = self.signal_logs
        
        if timeframe:
            filtered_logs = [log for log in filtered_logs if log["timeframe"] == timeframe]
            
        if direction:
            filtered_logs = [log for log in filtered_logs if log["direction"] == direction]
            
        return filtered_logs
    
    def get_conflict_logs(self, conflict_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get conflict logs, optionally filtered by conflict type.
        
        Args:
            conflict_type: Optional conflict type filter
            
        Returns:
            List of conflict log entries
        """
        if not self.enabled:
            return []
            
        filtered_logs = self.conflict_logs
        
        if conflict_type:
            filtered_logs = [log for log in filtered_logs if log["conflict_type"] == conflict_type]
            
        return filtered_logs
    
    def get_trade_logs(self, action: Optional[str] = None, timeframe: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get trade logs, optionally filtered by action and timeframe.
        
        Args:
            action: Optional action filter
            timeframe: Optional timeframe filter
            
        Returns:
            List of trade log entries
        """
        if not self.enabled:
            return []
            
        filtered_logs = self.trade_logs
        
        if action:
            filtered_logs = [log for log in filtered_logs if log["action"] == action]
            
        if timeframe:
            filtered_logs = [log for log in filtered_logs if log["timeframe"] == timeframe]
            
        return filtered_logs
    
    def export_to_json(self, filename: Optional[str] = None) -> str:
        """
        Export all logs to a JSON file.
        
        Args:
            filename: Optional filename for the export
            
        Returns:
            Path to the exported file
        """
        if not self.enabled:
            return ""
            
        # Create export data
        export_data = {
            "session_id": self.session_id,
            "exported_at": datetime.now().isoformat(),
            "signals": self.signal_logs,
            "conflicts": self.conflict_logs,
            "trades": self.trade_logs,
            "indicators": self.indicator_logs,
            "system": self.system_logs
        }
        
        # Generate filename if not provided
        if not filename:
            filename = f"strategy_log_{self.session_id}.json"
            
        # Ensure .json extension
        if not filename.endswith('.json'):
            filename += '.json'
            
        # Create full path
        file_path = os.path.join(self.log_dir, filename)
        
        # Write to file
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        logger.info(f"Strategy logs exported to {file_path}")
        
        return file_path
    
    def export_to_csv(self, directory: Optional[str] = None) -> Dict[str, str]:
        """
        Export logs to separate CSV files by type.
        
        Args:
            directory: Optional directory for the export
            
        Returns:
            Dictionary of log types and file paths
        """
        if not self.enabled:
            return {}
            
        # Use provided directory or default
        export_dir = directory or os.path.join(self.log_dir, f"export_{self.session_id}")
        
        # Create directory if it doesn't exist
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
            
        # Export each log type to a separate CSV
        file_paths = {}
        
        # Export signals
        if self.signal_logs:
            signals_df = pd.DataFrame(self.signal_logs)
            signals_path = os.path.join(export_dir, f"signals_{self.session_id}.csv")
            signals_df.to_csv(signals_path, index=False)
            file_paths["signals"] = signals_path
            
        # Export conflicts
        if self.conflict_logs:
            conflicts_df = pd.DataFrame(self.conflict_logs)
            conflicts_path = os.path.join(export_dir, f"conflicts_{self.session_id}.csv")
            conflicts_df.to_csv(conflicts_path, index=False)
            file_paths["conflicts"] = conflicts_path
            
        # Export trades
        if self.trade_logs:
            trades_df = pd.DataFrame(self.trade_logs)
            trades_path = os.path.join(export_dir, f"trades_{self.session_id}.csv")
            trades_df.to_csv(trades_path, index=False)
            file_paths["trades"] = trades_path
            
        # Export indicators (might be large, so only export if specifically requested)
        if self.indicator_logs:
            indicators_df = pd.DataFrame(self.indicator_logs)
            indicators_path = os.path.join(export_dir, f"indicators_{self.session_id}.csv")
            indicators_df.to_csv(indicators_path, index=False)
            file_paths["indicators"] = indicators_path
            
        # Export system logs
        if self.system_logs:
            system_df = pd.DataFrame(self.system_logs)
            system_path = os.path.join(export_dir, f"system_{self.session_id}.csv")
            system_df.to_csv(system_path, index=False)
            file_paths["system"] = system_path
            
        logger.info(f"Strategy logs exported as CSV to {export_dir}")
        
        return file_paths
    
    def clear_logs(self) -> None:
        """
        Clear all logs.
        """
        if not self.enabled:
            return
            
        self.signal_logs = []
        self.conflict_logs = []
        self.trade_logs = []
        self.indicator_logs = []
        self.system_logs = []
        
        logger.info("Strategy logs cleared")
    
    def get_log_counts(self) -> Dict[str, int]:
        """
        Get counts of different log types.
        
        Returns:
            Dictionary of log types and counts
        """
        if not self.enabled:
            return {}
            
        return {
            "signals": len(self.signal_logs),
            "conflicts": len(self.conflict_logs),
            "trades": len(self.trade_logs),
            "indicators": len(self.indicator_logs),
            "system": len(self.system_logs)
        }


# Helper functions for easier access

def get_strategy_logger() -> StrategyLogger:
    """
    Get the global strategy logger instance.
    
    Returns:
        StrategyLogger instance
    """
    return StrategyLogger()

def log_strategy_signal(timeframe: str, direction: str, reason: str, **details) -> None:
    """
    Log a strategy signal using the global logger.
    
    Args:
        timeframe: Signal timeframe
        direction: Signal direction (LONG/SHORT)
        reason: Reason for the signal
        **details: Additional signal details
    """
    logger = get_strategy_logger()
    logger.log_signal(timeframe, direction, reason, **details)

def log_strategy_conflict(timeframes: List[str], conflict_type: str, resolution: str, **details) -> None:
    """
    Log a strategy conflict using the global logger.
    
    Args:
        timeframes: List of timeframes involved in the conflict
        conflict_type: Type of conflict
        resolution: How the conflict was resolved
        **details: Additional conflict details
    """
    logger = get_strategy_logger()
    logger.log_conflict(timeframes, conflict_type, resolution, **details)

def log_strategy_trade(action: str, timeframe: str, direction: str, **details) -> None:
    """
    Log a trade action using the global logger.
    
    Args:
        action: Trade action (ENTRY, EXIT, STOP, TARGET)
        timeframe: Trade timeframe
        direction: Trade direction (LONG/SHORT)
        **details: Additional trade details
    """
    logger = get_strategy_logger()
    logger.log_trade(action, timeframe, direction, **details)
