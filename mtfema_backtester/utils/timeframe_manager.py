"""
Timeframe management system for MT 9 EMA Backtester.

This module provides a comprehensive system for managing timeframes,
including conversion between different timeframe notations, hierarchical 
relationships, and proper aggregation of data across timeframes.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Union, Optional, Any, Tuple
import re

logger = logging.getLogger(__name__)

class TimeframeManager:
    """
    Manages timeframe conversion, relationships, and hierarchies.
    
    Features:
    - Standardized timeframe notation
    - Conversion between different timeframe formats
    - Hierarchy determination for progressive targeting
    - Data aggregation across timeframes
    """
    
    # Timeframe maps with their characteristics
    TIMEFRAME_MAP = {
        "1m": {"chartDescription": "Min", "chartUnit": "m", "chartUnits": 1, "minutes": 1},
        "5m": {"chartDescription": "Min", "chartUnit": "m", "chartUnits": 5, "minutes": 5},
        "15m": {"chartDescription": "Min", "chartUnit": "m", "chartUnits": 15, "minutes": 15},
        "30m": {"chartDescription": "Min", "chartUnit": "m", "chartUnits": 30, "minutes": 30},
        "1h": {"chartDescription": "Hour", "chartUnit": "h", "chartUnits": 1, "minutes": 60},
        "4h": {"chartDescription": "Hour", "chartUnit": "h", "chartUnits": 4, "minutes": 240},
        "1d": {"chartDescription": "Day", "chartUnit": "d", "chartUnits": 1, "minutes": 1440},
        "1w": {"chartDescription": "Week", "chartUnit": "w", "chartUnits": 1, "minutes": 10080}
    }
    
    # Standard timeframe hierarchy from smallest to largest
    HIERARCHY = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1w"]
    
    # Mapping for broker-specific timeframe notations
    NOTATION_MAP = {
        "tradovate": {
            "1": "1m", "3": "3m", "5": "5m", "15": "15m", "30": "30m",
            "60": "1h", "240": "4h", "D": "1d", "W": "1w"
        },
        "rithmic": {
            "1minute": "1m", "5minute": "5m", "15minute": "15m", "30minute": "30m",
            "60minute": "1h", "240minute": "4h", "1day": "1d", "1week": "1w"
        },
        "metatrader": {
            "M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
            "H1": "1h", "H4": "4h", "D1": "1d", "W1": "1w"
        }
    }
    
    # Regex patterns for timeframe parsing
    TF_PATTERNS = {
        "standard": re.compile(r"^(\d+)([mhdw])$"),  # e.g., 1m, 4h, 1d
        "minutes": re.compile(r"^(\d+)$"),           # e.g., 1, 5, 15
        "text": re.compile(r"^(\d+)(min|hour|day|week).*$", re.IGNORECASE)  # e.g., 5min, 1hour
    }
    
    def __init__(self):
        """Initialize the timeframe manager."""
        logger.info("Timeframe manager initialized")
    
    def get_standard_timeframe(self, timeframe: str, broker: Optional[str] = None) -> str:
        """
        Convert any timeframe notation to the standard format.
        
        Args:
            timeframe: Timeframe in any notation
            broker: Optional broker name for specific notations
            
        Returns:
            Timeframe in standard format
        """
        # Already in standard format
        if timeframe in self.TIMEFRAME_MAP:
            return timeframe
            
        # Check broker-specific notations
        if broker and broker.lower() in self.NOTATION_MAP:
            broker_map = self.NOTATION_MAP[broker.lower()]
            if timeframe in broker_map:
                return broker_map[timeframe]
        
        # Try to parse with patterns
        standard_match = self.TF_PATTERNS["standard"].match(timeframe.lower())
        if standard_match:
            value, unit = standard_match.groups()
            return f"{value}{unit}"
            
        minutes_match = self.TF_PATTERNS["minutes"].match(timeframe)
        if minutes_match:
            minutes = int(minutes_match.group(1))
            # Convert minutes to standard format
            if minutes < 60:
                return f"{minutes}m"
            elif minutes == 60:
                return "1h"
            elif minutes == 240:
                return "4h"
            elif minutes == 1440:
                return "1d"
            elif minutes == 10080:
                return "1w"
                
        text_match = self.TF_PATTERNS["text"].match(timeframe.lower())
        if text_match:
            value, unit_text = text_match.groups()
            if "min" in unit_text:
                return f"{value}m"
            elif "hour" in unit_text:
                return f"{value}h"
            elif "day" in unit_text:
                return f"{value}d"
            elif "week" in unit_text:
                return f"{value}w"
        
        # If all else fails, log a warning and return the original
        logger.warning(f"Unknown timeframe format: {timeframe}, using as-is")
        return timeframe
    
    def get_minutes(self, timeframe: str) -> int:
        """
        Get the number of minutes in a timeframe.
        
        Args:
            timeframe: Timeframe in standard format
            
        Returns:
            Number of minutes
        """
        standard_tf = self.get_standard_timeframe(timeframe)
        
        if standard_tf in self.TIMEFRAME_MAP:
            return self.TIMEFRAME_MAP[standard_tf]["minutes"]
            
        # Try to parse manually
        try:
            standard_match = self.TF_PATTERNS["standard"].match(standard_tf.lower())
            if standard_match:
                value, unit = standard_match.groups()
                value = int(value)
                
                if unit == "m":
                    return value
                elif unit == "h":
                    return value * 60
                elif unit == "d":
                    return value * 1440
                elif unit == "w":
                    return value * 10080
        except Exception as e:
            logger.error(f"Error parsing timeframe: {e}")
            
        logger.warning(f"Could not determine minutes for timeframe: {timeframe}")
        return 0
    
    def get_description(self, timeframe: str) -> str:
        """
        Get a human-readable description of a timeframe.
        
        Args:
            timeframe: Timeframe in standard format
            
        Returns:
            Human-readable description
        """
        standard_tf = self.get_standard_timeframe(timeframe)
        
        if standard_tf in self.TIMEFRAME_MAP:
            tf_info = self.TIMEFRAME_MAP[standard_tf]
            if tf_info["chartUnits"] == 1:
                return f"1 {tf_info['chartDescription']}"
            else:
                return f"{tf_info['chartUnits']} {tf_info['chartDescription']}s"
                
        # Try to parse manually
        standard_match = self.TF_PATTERNS["standard"].match(standard_tf.lower())
        if standard_match:
            value, unit = standard_match.groups()
            
            if unit == "m":
                return f"{value} Minute{'s' if int(value) > 1 else ''}"
            elif unit == "h":
                return f"{value} Hour{'s' if int(value) > 1 else ''}"
            elif unit == "d":
                return f"{value} Day{'s' if int(value) > 1 else ''}"
            elif unit == "w":
                return f"{value} Week{'s' if int(value) > 1 else ''}"
                
        return standard_tf
    
    def is_higher_timeframe(self, tf1: str, tf2: str) -> bool:
        """
        Check if tf1 is a higher timeframe than tf2.
        
        Args:
            tf1: First timeframe
            tf2: Second timeframe
            
        Returns:
            True if tf1 is higher than tf2
        """
        minutes1 = self.get_minutes(tf1)
        minutes2 = self.get_minutes(tf2)
        
        return minutes1 > minutes2
    
    def get_next_higher_timeframe(self, timeframe: str) -> Optional[str]:
        """
        Get the next higher timeframe in the hierarchy.
        
        Args:
            timeframe: Current timeframe
            
        Returns:
            Next higher timeframe or None if already at highest
        """
        standard_tf = self.get_standard_timeframe(timeframe)
        
        try:
            current_index = self.HIERARCHY.index(standard_tf)
            if current_index < len(self.HIERARCHY) - 1:
                return self.HIERARCHY[current_index + 1]
        except ValueError:
            # If not in standard hierarchy, find by minutes
            minutes = self.get_minutes(timeframe)
            for tf in self.HIERARCHY:
                if self.get_minutes(tf) > minutes:
                    return tf
                    
        return None
    
    def get_timeframe_hierarchy(self, timeframes: List[str]) -> List[str]:
        """
        Sort timeframes in ascending order of size.
        
        Args:
            timeframes: List of timeframes in any format
            
        Returns:
            Sorted list of timeframes in standard format
        """
        # Convert to standard format first
        standard_tfs = [self.get_standard_timeframe(tf) for tf in timeframes]
        
        # Try to use standard hierarchy if all timeframes are recognized
        if all(tf in self.HIERARCHY for tf in standard_tfs):
            return sorted(standard_tfs, key=lambda tf: self.HIERARCHY.index(tf))
            
        # Otherwise sort by minutes
        return sorted(standard_tfs, key=self.get_minutes)
    
    def get_aggregation_rule(self, source_tf: str, target_tf: str) -> Optional[str]:
        """
        Get the pandas resampling rule to convert from source to target timeframe.
        
        Args:
            source_tf: Source timeframe
            target_tf: Target timeframe
            
        Returns:
            Pandas resampling rule or None if invalid
        """
        source_minutes = self.get_minutes(source_tf)
        target_minutes = self.get_minutes(target_tf)
        
        # Cannot aggregate to a smaller timeframe
        if target_minutes < source_minutes:
            logger.warning(f"Cannot aggregate from {source_tf} to {target_tf} (smaller timeframe)")
            return None
            
        # No need to aggregate same timeframe
        if target_minutes == source_minutes:
            return None
            
        # Generate appropriate rule based on target
        standard_tf = self.get_standard_timeframe(target_tf)
        standard_match = self.TF_PATTERNS["standard"].match(standard_tf.lower())
        
        if standard_match:
            value, unit = standard_match.groups()
            return f"{value}{unit.upper()}"
            
        # If all else fails, use minutes
        return f"{target_minutes}min"
    
    def resample_data(self, 
                     data: pd.DataFrame, 
                     source_tf: str, 
                     target_tf: str,
                     ohlc_only: bool = False) -> pd.DataFrame:
        """
        Resample data from source to target timeframe.
        
        Args:
            data: DataFrame with timeseries data
            source_tf: Source timeframe
            target_tf: Target timeframe
            ohlc_only: Whether to only include OHLC columns
            
        Returns:
            Resampled DataFrame
        """
        rule = self.get_aggregation_rule(source_tf, target_tf)
        
        if rule is None:
            return data
        
        # Ensure data is sorted by index
        data = data.sort_index()
        
        # Create aggregation dictionary for each column
        agg_dict = {}
        
        # Always handle OHLC columns
        if 'open' in data.columns:
            agg_dict['open'] = 'first'
        if 'high' in data.columns:
            agg_dict['high'] = 'max'
        if 'low' in data.columns:
            agg_dict['low'] = 'min'
        if 'close' in data.columns:
            agg_dict['close'] = 'last'
        if 'volume' in data.columns:
            agg_dict['volume'] = 'sum'
            
        # Handle other columns if not OHLC only
        if not ohlc_only:
            for col in data.columns:
                if col not in agg_dict:
                    if 'ema' in col.lower() or 'ma' in col.lower() or 'avg' in col.lower():
                        agg_dict[col] = 'last'
                    elif 'volume' in col.lower() or 'qty' in col.lower():
                        agg_dict[col] = 'sum'
                    elif 'rsi' in col.lower() or 'indicator' in col.lower():
                        agg_dict[col] = 'last'
                    else:
                        # Default to last value
                        agg_dict[col] = 'last'
        
        # Perform resampling
        resampled = data.resample(rule).agg(agg_dict)
        
        # Forward fill NaN values that may have been introduced
        resampled = resampled.ffill()
        
        logger.info(f"Resampled data from {source_tf} to {target_tf} using rule {rule}")
        
        return resampled
    
    def get_target_timeframe_sequence(self, entry_timeframe: str) -> List[str]:
        """
        Get the sequence of target timeframes for progressive targeting.
        
        Args:
            entry_timeframe: Entry timeframe
            
        Returns:
            List of target timeframes in order
        """
        standard_tf = self.get_standard_timeframe(entry_timeframe)
        
        try:
            index = self.HIERARCHY.index(standard_tf)
            # Return all higher timeframes
            return self.HIERARCHY[index+1:]
        except ValueError:
            # If not in standard hierarchy, find by minutes
            minutes = self.get_minutes(entry_timeframe)
            return [tf for tf in self.HIERARCHY if self.get_minutes(tf) > minutes]
    
    def get_timeframe_factor(self, source_tf: str, target_tf: str) -> float:
        """
        Get the ratio between target and source timeframes.
        
        Args:
            source_tf: Source timeframe
            target_tf: Target timeframe
            
        Returns:
            Ratio of target minutes to source minutes
        """
        source_minutes = self.get_minutes(source_tf)
        target_minutes = self.get_minutes(target_tf)
        
        if source_minutes == 0:
            logger.warning(f"Invalid source timeframe: {source_tf}")
            return 1.0
            
        return target_minutes / source_minutes


# Create global instance for convenience
_timeframe_manager = TimeframeManager()

def get_timeframe_manager() -> TimeframeManager:
    """
    Get the global timeframe manager instance.
    
    Returns:
        TimeframeManager instance
    """
    return _timeframe_manager
