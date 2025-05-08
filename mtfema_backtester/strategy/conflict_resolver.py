"""
Conflict resolver for the Multi-Timeframe 9 EMA Extension Strategy Backtester.

This module detects and resolves conflicts between different timeframes
to adjust trade parameters and risk accordingly.
"""

import logging
import pandas as pd
import numpy as np

from mtfema_backtester.utils.timeframe_utils import (
    get_timeframe_minutes, 
    map_timestamp_to_higher_timeframe
)

logger = logging.getLogger(__name__)
"""
Enhanced conflict resolution system for MT 9 EMA Backtester.

This module provides sophisticated conflict detection and resolution
across timeframes, with quantitative scoring for more nuanced risk adjustment.
"""

import logging
import math
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
import pandas as pd
from ..utils.performance_monitor import time_operation
from ..utils.strategy_logger import log_strategy_conflict

logger = logging.getLogger(__name__)

class ConflictType:
    """Constants for conflict types."""
    NO_CONFLICT = "NoConflict"
    CONSOLIDATION = "Consolidation"
    DIRECT_CORRECTION = "DirectCorrection"
    TRAP_SETUP = "TrapSetup"
    EXHAUSTION = "Exhaustion"
    DIVERGENCE = "Divergence"


class ConflictResolver:
    """
    Enhanced system for detecting and resolving timeframe conflicts.
    
    Features:
    - Sophisticated conflict detection with multiple conflict types
    - Quantitative conflict scoring based on angle differences
    - Nuanced risk adjustment based on conflict severity
    - Detailed conflict logging for strategy analysis
    """
    
    def __init__(self, timeframe_hierarchy: List[str]):
        """
        Initialize the conflict resolver.
        
        Args:
            timeframe_hierarchy: List of timeframes in ascending order
        """
        self.timeframe_hierarchy = timeframe_hierarchy
        logger.info(f"Conflict resolver initialized with timeframe hierarchy: {timeframe_hierarchy}")
    
    @time_operation
    def resolve_timeframe_conflicts(self, 
                                   timeframe_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Detect and resolve conflicts between timeframes.
        
        Args:
            timeframe_data: Dictionary of timeframe data objects
            
        Returns:
            Dictionary of conflict resolutions by timeframe pair
        """
        conflict_resolutions = {}
        
        # Process only timeframes that are in our hierarchy
        valid_timeframes = [tf for tf in self.timeframe_hierarchy if tf in timeframe_data]
        valid_timeframes.sort(key=lambda tf: self.timeframe_hierarchy.index(tf))
        
        # Check for conflicts between consecutive timeframes
        for i in range(len(valid_timeframes) - 1):
            lower_tf = valid_timeframes[i]
            higher_tf = valid_timeframes[i + 1]
            
            lower_tf_data = timeframe_data[lower_tf]
            higher_tf_data = timeframe_data[higher_tf]
            
            # Skip if not enough data
            if not hasattr(lower_tf_data, 'has_extension') or not hasattr(higher_tf_data, 'has_extension'):
                continue
                
            pair_key = f"{lower_tf}_{higher_tf}"
            
            # Detect specific conflict type
            conflict_type, details = self._detect_conflict_type(lower_tf_data, higher_tf_data)
            
            # Create resolution with default risk factor
            resolution = {
                'type': conflict_type,
                'risk_factor': 1.0,  # Default to full risk
                'details': details
            }
            
            # Adjust risk factor based on conflict type and severity
            if conflict_type != ConflictType.NO_CONFLICT:
                resolution['risk_factor'] = self._calculate_risk_factor(conflict_type, details)
                
                # Log the conflict
                log_strategy_conflict(
                    timeframes=[lower_tf, higher_tf],
                    conflict_type=conflict_type,
                    resolution=f"Risk adjusted to {resolution['risk_factor']:.2f}",
                    severity=details.get('severity', 'medium'),
                    risk_factor=resolution['risk_factor']
                )
            
            conflict_resolutions[pair_key] = resolution
        
        return conflict_resolutions
    
    @time_operation
    def _detect_conflict_type(self, 
                             lower_tf_data: Any, 
                             higher_tf_data: Any) -> Tuple[str, Dict[str, Any]]:
        """
        Detect the specific type of conflict between timeframes.
        
        Args:
            lower_tf_data: Data for the lower timeframe
            higher_tf_data: Data for the higher timeframe
            
        Returns:
            Tuple of (conflict_type, details_dict)
        """
        # Extract trend directions
        lower_trend = self._get_trend_direction(lower_tf_data)
        higher_trend = self._get_trend_direction(higher_tf_data)
        
        # Calculate trend angle difference (0-180 degrees)
        angle_diff = self._calculate_angle_difference(lower_tf_data, higher_tf_data)
        
        # Get extension states
        lower_extended = getattr(lower_tf_data, 'has_extension', False)
        higher_extended = getattr(higher_tf_data, 'has_extension', False)
        
        # Initialize details
        details = {
            'lower_trend': lower_trend,
            'higher_trend': higher_trend,
            'angle_difference': angle_diff,
            'lower_extended': lower_extended,
            'higher_extended': higher_extended
        }
        
        # Determine conflict type based on trend directions and extensions
        
        # No conflict: Same direction
        if lower_trend == higher_trend:
            return ConflictType.NO_CONFLICT, details
        
        # Direct correction: Opposite directions with both extended
        if lower_trend != higher_trend and lower_extended and higher_extended:
            severity = 'high' if angle_diff > 135 else 'medium'
            details['severity'] = severity
            return ConflictType.DIRECT_CORRECTION, details
            
        # Consolidation: Opposite directions but higher timeframe not extended
        if lower_trend != higher_trend and lower_extended and not higher_extended:
            severity = 'medium' if angle_diff > 90 else 'low'
            details['severity'] = severity
            return ConflictType.CONSOLIDATION, details
            
        # Trap setup: Lower not extended but higher is extended in opposite direction
        if lower_trend != higher_trend and not lower_extended and higher_extended:
            severity = 'high' if angle_diff > 120 else 'medium'
            details['severity'] = severity
            return ConflictType.TRAP_SETUP, details
        
        # Exhaustion: Trends appear to be reversing
        if hasattr(lower_tf_data, 'momentum') and hasattr(higher_tf_data, 'momentum'):
            lower_momentum = lower_tf_data.momentum
            higher_momentum = higher_tf_data.momentum
            
            # Conflicting momentum signatures
            if lower_momentum * higher_momentum < 0:  # Opposite signs
                details['lower_momentum'] = lower_momentum
                details['higher_momentum'] = higher_momentum
                details['severity'] = 'medium'
                return ConflictType.EXHAUSTION, details
                
        # Divergence: Price extended but indicators suggest reversal
        if hasattr(lower_tf_data, 'has_divergence') and lower_tf_data.has_divergence:
            details['divergence_type'] = getattr(lower_tf_data, 'divergence_type', 'unknown')
            details['severity'] = 'medium'
            return ConflictType.DIVERGENCE, details
        
        # Default to no conflict if no specific conditions met
        return ConflictType.NO_CONFLICT, details
    
    def _get_trend_direction(self, tf_data: Any) -> str:
        """
        Get the trend direction from timeframe data.
        
        Args:
            tf_data: Timeframe data object
            
        Returns:
            "up", "down", or "neutral"
        """
        # Try different attributes that might indicate trend
        if hasattr(tf_data, 'trend_direction'):
            return tf_data.trend_direction
            
        if hasattr(tf_data, 'ema_slope'):
            slope = tf_data.ema_slope
            if slope > 0.01:
                return "up"
            elif slope < -0.01:
                return "down"
            else:
                return "neutral"
        
        # If data has Paper Feet color        
        if hasattr(tf_data, 'paper_feet_color'):
            color = tf_data.paper_feet_color
            if color == 2:  # Green
                return "up"
            elif color == 0:  # Red
                return "down"
            else:  # Yellow
                return "neutral"
                
        # If has extension direction
        if hasattr(tf_data, 'extension_direction'):
            return "up" if tf_data.extension_direction > 0 else "down"
            
        # Default to neutral if no direction indicators available
        return "neutral"
    
    def _calculate_angle_difference(self, 
                                   lower_tf_data: Any, 
                                   higher_tf_data: Any) -> float:
        """
        Calculate the angle difference between two timeframe trends.
        
        Args:
            lower_tf_data: Data for the lower timeframe
            higher_tf_data: Data for the higher timeframe
            
        Returns:
            Angle difference in degrees (0-180)
        """
        # Try to get slope values
        lower_slope = self._get_trend_slope(lower_tf_data)
        higher_slope = self._get_trend_slope(higher_tf_data)
        
        # Convert slopes to angles (in degrees)
        lower_angle = math.degrees(math.atan(lower_slope))
        higher_angle = math.degrees(math.atan(higher_slope))
        
        # Calculate absolute difference between angles
        angle_diff = abs(lower_angle - higher_angle)
        
        # Ensure result is between 0 and 180 degrees
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
            
        return angle_diff
    
    def _get_trend_slope(self, tf_data: Any) -> float:
        """
        Get the trend slope from timeframe data.
        
        Args:
            tf_data: Timeframe data object
            
        Returns:
            Slope value
        """
        # Try different attributes that might contain slope information
        if hasattr(tf_data, 'ema_slope'):
            return tf_data.ema_slope
            
        if hasattr(tf_data, 'trend_slope'):
            return tf_data.trend_slope
            
        # Calculate from extension if available
        if hasattr(tf_data, 'extension_percent') and hasattr(tf_data, 'extension_direction'):
            extension = tf_data.extension_percent
            direction = 1 if tf_data.extension_direction > 0 else -1
            return extension * direction * 0.01  # Scale to reasonable slope
            
        # Default to neutral slope if not available
        return 0.0
    
    def _calculate_risk_factor(self, conflict_type: str, details: Dict[str, Any]) -> float:
        """
        Calculate risk adjustment factor based on conflict details.
        
        Args:
            conflict_type: Type of conflict detected
            details: Conflict details dictionary
            
        Returns:
            Risk factor (0.0-1.0)
        """
        # Default risk factor
        base_risk = 1.0
        
        # Adjust based on conflict type
        if conflict_type == ConflictType.NO_CONFLICT:
            return base_risk
            
        # Get angle difference for severity calculation
        angle_diff = details.get('angle_difference', 0)
        
        # Get severity if provided
        severity = details.get('severity', 'medium')
        severity_factor = 0.5  # Default medium
        
        if severity == 'low':
            severity_factor = 0.8
        elif severity == 'medium':
            severity_factor = 0.5
        elif severity == 'high':
            severity_factor = 0.2
            
        # Apply risk adjustments based on conflict type
        if conflict_type == ConflictType.DIRECT_CORRECTION:
            # Direct correction is very high risk
            return base_risk * severity_factor * 0.5
            
        elif conflict_type == ConflictType.CONSOLIDATION:
            # Consolidation is medium risk
            return base_risk * severity_factor * 0.8
            
        elif conflict_type == ConflictType.TRAP_SETUP:
            # Trap setups are high risk
            return base_risk * severity_factor * 0.3
            
        elif conflict_type == ConflictType.EXHAUSTION:
            # Exhaustion depends on momentum strength
            momentum_factor = 0.6
            if 'lower_momentum' in details and 'higher_momentum' in details:
                # Higher momentum difference means higher risk
                momentum_diff = abs(details['lower_momentum'] - details['higher_momentum'])
                momentum_factor = max(0.2, 1.0 - (momentum_diff / 2.0))
            return base_risk * severity_factor * momentum_factor
            
        elif conflict_type == ConflictType.DIVERGENCE:
            # Divergence is moderately high risk
            divergence_factor = 0.7
            return base_risk * severity_factor * divergence_factor
            
        # Default fallback - reduce risk moderately
        return base_risk * 0.7
    
    def aggregate_risk_factor(self, conflict_resolutions: Dict[str, Dict[str, Any]]) -> float:
        """
        Aggregate risk factors from multiple timeframe conflicts.
        
        Args:
            conflict_resolutions: Dictionary of conflict resolutions
            
        Returns:
            Aggregated risk factor
        """
        if not conflict_resolutions:
            return 1.0
            
        # Extract risk factors
        risk_factors = [r['risk_factor'] for r in conflict_resolutions.values()]
        
        # Use the minimum risk factor as the most conservative approach
        return min(risk_factors)
    
    def check_conflict_for_timeframe(self, 
                                    timeframe: str, 
                                    conflict_resolutions: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Check if a timeframe is involved in any conflicts.
        
        Args:
            timeframe: Timeframe to check
            conflict_resolutions: Dictionary of conflict resolutions
            
        Returns:
            Conflict resolution dictionary or None if no conflicts
        """
        for pair_key, resolution in conflict_resolutions.items():
            if timeframe in pair_key.split('_'):
                return resolution
                
        return None
# Conflict types
class ConflictType:
    """Enum-like class for conflict types"""
    NO_CONFLICT = "NoConflict"
    DIRECT_CORRECTION = "DirectCorrection"
    TRAP_SETUP = "TrapSetup"
    CONSOLIDATION = "Consolidation"
    NO_DATA = "NoData"
    DATA_ERROR = "DataError"

def check_timeframe_conflict(timeframe_data, current_tf, higher_tf, timestamp):
    """
    Check for conflicts between current and higher timeframe.
    
    Args:
        timeframe_data: TimeframeData instance with indicator data
        current_tf: Current timeframe string
        higher_tf: Higher timeframe string
        timestamp: Timestamp to check
        
    Returns:
        str: Conflict type (see ConflictType class)
    """
    # Get extension data
    current_ext = timeframe_data.get_indicator(current_tf, "ExtensionSignal")
    higher_ext = timeframe_data.get_indicator(higher_tf, "ExtensionSignal")
    
    if current_ext is None or higher_ext is None:
        logger.warning(f"Missing extension data for conflict check: current_tf={current_tf}, higher_tf={higher_tf}")
        return ConflictType.NO_DATA
    
    # Get current values
    current_idx = timestamp
    higher_idx = map_timestamp_to_higher_timeframe(timestamp, current_tf, higher_tf)
    
    try:
        # Check if both have extensions but in opposite directions
        current_has_extension = _get_value(current_ext, current_idx, 'has_extension', False)
        higher_has_extension = _get_value(higher_ext, higher_idx, 'has_extension', False)
        
        if current_has_extension and higher_has_extension:
            current_up = _get_value(current_ext, current_idx, 'extended_up', False)
            current_down = _get_value(current_ext, current_idx, 'extended_down', False)
            higher_up = _get_value(higher_ext, higher_idx, 'extended_up', False)
            higher_down = _get_value(higher_ext, higher_idx, 'extended_down', False)
            
            if (current_up and higher_down) or (current_down and higher_up):
                logger.info(f"Direct correction conflict detected: {current_tf} vs {higher_tf}")
                return ConflictType.DIRECT_CORRECTION
        
        # Check for trap setup
        if higher_has_extension and not current_has_extension:
            # Check reclamation in lower timeframe
            reclamation = timeframe_data.get_indicator(current_tf, "Reclamation")
            if reclamation is not None:
                has_bullish_reclaim = _get_value(reclamation, current_idx, 'BullishReclaim', False)
                has_bearish_reclaim = _get_value(reclamation, current_idx, 'BearishReclaim', False)
                
                if has_bullish_reclaim or has_bearish_reclaim:
                    logger.info(f"Trap setup detected: {current_tf} reclamation against {higher_tf} extension")
                    return ConflictType.TRAP_SETUP
                
            logger.info(f"Consolidation detected: {higher_tf} extended but {current_tf} not extended")
            return ConflictType.CONSOLIDATION
        
        logger.debug(f"No conflict detected between {current_tf} and {higher_tf}")
        return ConflictType.NO_CONFLICT
        
    except (KeyError, IndexError, TypeError) as e:
        logger.error(f"Error checking timeframe conflict: {str(e)}")
        return ConflictType.DATA_ERROR

def adjust_risk_for_conflict(base_risk, conflict_type):
    """
    Adjust risk percentage based on conflict type.
    
    Args:
        base_risk: Base risk percentage (e.g., 0.01 for 1%)
        conflict_type: Type of conflict detected
        
    Returns:
        float: Adjusted risk percentage
    """
    if conflict_type == ConflictType.DIRECT_CORRECTION:
        # High-risk situation - reduce risk by 75%
        return base_risk * 0.25
    
    elif conflict_type == ConflictType.TRAP_SETUP:
        # Moderate-risk situation - reduce risk by 50%
        return base_risk * 0.5
    
    elif conflict_type == ConflictType.CONSOLIDATION:
        # Slightly higher risk - reduce risk by 25%
        return base_risk * 0.75
    
    elif conflict_type in [ConflictType.DATA_ERROR, ConflictType.NO_DATA]:
        # Uncertain situation - reduce risk by 50%
        return base_risk * 0.5
    
    # No conflict or unknown - use base risk
    return base_risk

def get_target_for_timeframe(timeframe_data, target_tf, signal_type):
    """
    Get the target price for a specific timeframe.
    
    Args:
        timeframe_data: TimeframeData instance
        target_tf: Target timeframe string
        signal_type: Signal type ('LONG' or 'SHORT')
        
    Returns:
        float: Target price, or None if not available
    """
    # Get 9 EMA value for target timeframe
    ema_data = timeframe_data.get_indicator(target_tf, "EMA_9")
    if ema_data is None or ema_data.empty:
        logger.warning(f"No EMA data available for target timeframe {target_tf}")
        return None
    
    # Get the latest value
    try:
        latest_ema = ema_data.iloc[-1]
        if isinstance(latest_ema, pd.Series):
            latest_ema = latest_ema.iloc[0]
        
        logger.info(f"Target for {signal_type} on {target_tf}: {latest_ema}")
        return float(latest_ema)
    
    except (IndexError, TypeError) as e:
        logger.error(f"Error getting target for timeframe {target_tf}: {str(e)}")
        return None

def _get_value(df, idx, column, default=None):
    """
    Helper function to safely get value from DataFrame.
    
    Args:
        df: DataFrame to get value from
        idx: Index to get
        column: Column name
        default: Default value if not found
        
    Returns:
        Value at df.loc[idx, column] or default if not found
    """
    try:
        if idx not in df.index or column not in df.columns:
            return default
        
        value = df.loc[idx, column]
        
        # Handle case where the value is a Series (handle MultiIndex)
        if isinstance(value, pd.Series):
            return value.iloc[0]
        
        return value
    
    except (KeyError, IndexError, TypeError) as e:
        logger.debug(f"Error getting value at {idx}, {column}: {str(e)}")
        return default 