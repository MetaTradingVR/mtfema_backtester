"""
Conflict Resolver for the Multi-Timeframe 9 EMA Extension Strategy.

This module handles the resolution of conflicts between different timeframes,
particularly when extensions and reclamations occur in opposite directions.
"""

import logging
import pandas as pd
import numpy as np

from mtfema_backtester.config import STRATEGY_PARAMS

logger = logging.getLogger(__name__)

# Define conflict types
class ConflictType:
    NO_CONFLICT = "no_conflict"  # No conflict detected
    CONSOLIDATION = "consolidation"  # Higher TF extended, lower TF around EMA
    DIRECT_CORRECTION = "direct_correction"  # TFs extended in opposite directions
    TRAP_SETUP = "trap_setup"  # Reclamation against prevailing higher TF extension

class ConflictResolver:
    """
    Resolves conflicts between multiple timeframes for the strategy.
    """
    
    def __init__(self, 
                 prioritize_higher_timeframe=None, 
                 minimum_agreement=None,
                 timeframe_weights=None):
        """
        Initialize the ConflictResolver
        
        Parameters:
        -----------
        prioritize_higher_timeframe : bool, optional
            Whether to prioritize higher timeframe signals over lower timeframes
        minimum_agreement : int, optional
            Minimum number of timeframes that must agree for valid signals
        timeframe_weights : dict, optional
            Weights for each timeframe in decision making
        """
        # Use provided values or defaults from config
        self.prioritize_higher_timeframe = prioritize_higher_timeframe
        if self.prioritize_higher_timeframe is None:
            self.prioritize_higher_timeframe = STRATEGY_PARAMS['conflict_resolution']['prioritize_higher_timeframe']
            
        self.minimum_agreement = minimum_agreement
        if self.minimum_agreement is None:
            self.minimum_agreement = STRATEGY_PARAMS['conflict_resolution']['minimum_agreement']
            
        self.timeframe_weights = timeframe_weights
        if self.timeframe_weights is None:
            self.timeframe_weights = STRATEGY_PARAMS['timeframe_weights']
        
        logger.info(f"ConflictResolver initialized with prioritize_higher_timeframe={self.prioritize_higher_timeframe}, "
                   f"minimum_agreement={self.minimum_agreement}")
    
    def detect_conflict(self, higher_tf_data, lower_tf_data):
        """
        Detect conflict between two timeframes
        
        Parameters:
        -----------
        higher_tf_data : dict
            Data for higher timeframe with extension info
        lower_tf_data : dict
            Data for lower timeframe with extension info
            
        Returns:
        --------
        str
            Conflict type from ConflictType
        """
        # Extract extension info
        higher_tf_extended = higher_tf_data.get('has_extension', False)
        higher_tf_extended_up = higher_tf_data.get('extended_up', False)
        higher_tf_extended_down = higher_tf_data.get('extended_down', False)
        
        lower_tf_extended = lower_tf_data.get('has_extension', False)
        lower_tf_extended_up = lower_tf_data.get('extended_up', False)
        lower_tf_extended_down = lower_tf_data.get('extended_down', False)
        
        lower_tf_reclaimed_up = lower_tf_data.get('reclaimed_up', False)
        lower_tf_reclaimed_down = lower_tf_data.get('reclaimed_down', False)
        
        # Case 1: Higher TF extended but lower TF not extended (consolidation)
        if higher_tf_extended and not lower_tf_extended:
            return ConflictType.CONSOLIDATION
        
        # Case 2: Higher TF and lower TF extended in opposite directions
        if higher_tf_extended and lower_tf_extended:
            if (higher_tf_extended_up and lower_tf_extended_down) or \
               (higher_tf_extended_down and lower_tf_extended_up):
                return ConflictType.DIRECT_CORRECTION
        
        # Case 3: Trap setup - reclamation against prevailing higher TF extension
        if higher_tf_extended:
            if (higher_tf_extended_up and lower_tf_reclaimed_down) or \
               (higher_tf_extended_down and lower_tf_reclaimed_up):
                return ConflictType.TRAP_SETUP
        
        # No conflict detected
        return ConflictType.NO_CONFLICT
    
    def resolve_conflict(self, conflict_type, signal, risk_params):
        """
        Resolve conflict by adjusting signal parameters
        
        Parameters:
        -----------
        conflict_type : str
            Conflict type from ConflictType
        signal : dict
            Signal information to be adjusted
        risk_params : dict
            Risk parameters to be adjusted
            
        Returns:
        --------
        tuple
            (adjusted_signal, adjusted_risk_params)
        """
        # Create copies to avoid modifying originals
        signal_copy = signal.copy()
        risk_params_copy = risk_params.copy()
        
        if conflict_type == ConflictType.NO_CONFLICT:
            # No adjustments needed
            return signal_copy, risk_params_copy
        
        elif conflict_type == ConflictType.TRAP_SETUP:
            # Trap setup - reduce risk and tighten targets
            logger.info(f"Resolving TRAP_SETUP conflict by reducing risk and tightening targets")
            
            # Reduce risk by 50%
            risk_params_copy['max_risk_per_trade'] = risk_params['max_risk_per_trade'] * 0.5
            
            # Tighter target - only target next timeframe
            signal_copy['max_progression_level'] = 1  # Limit to one progression
            
            # Add confidence measure
            signal_copy['confidence'] = 'low'
            signal_copy['conflict_resolution'] = 'trap_setup_adjustment'
            
            return signal_copy, risk_params_copy
        
        elif conflict_type == ConflictType.DIRECT_CORRECTION:
            # Direct correction - reduce risk and prepare for counter-trend
            logger.info(f"Resolving DIRECT_CORRECTION conflict by reducing risk")
            
            # Reduce risk by 50%
            risk_params_copy['max_risk_per_trade'] = risk_params['max_risk_per_trade'] * 0.5
            
            # Add confidence measure
            signal_copy['confidence'] = 'medium'
            signal_copy['conflict_resolution'] = 'direct_correction_adjustment'
            
            return signal_copy, risk_params_copy
        
        elif conflict_type == ConflictType.CONSOLIDATION:
            # Consolidation - maintain standard risk but watch for breakout
            logger.info(f"Resolving CONSOLIDATION conflict - standard risk, watching for breakout")
            
            # Standard risk, add note for monitoring
            signal_copy['monitor_for_breakout'] = True
            signal_copy['confidence'] = 'medium'
            signal_copy['conflict_resolution'] = 'consolidation_monitoring'
            
            return signal_copy, risk_params_copy
        
        # Default fallback
        return signal_copy, risk_params_copy
    
    def check_timeframe_agreement(self, extensions_by_timeframe, direction):
        """
        Check agreement across timeframes for a particular direction
        
        Parameters:
        -----------
        extensions_by_timeframe : dict
            Dictionary with extension data for each timeframe
        direction : str
            Direction to check agreement for ('long' or 'short')
            
        Returns:
        --------
        tuple
            (agreement_count, agreement_ratio, weighted_agreement)
        """
        is_long = direction == 'long'
        
        # Count agreements and calculate weighted agreement
        agreement_count = 0
        weighted_agreement = 0
        total_weight = 0
        
        for tf, ext_data in extensions_by_timeframe.items():
            # Get timeframe weight
            tf_weight = self.timeframe_weights.get(tf, 1.0)
            total_weight += tf_weight
            
            # Check for agreement based on direction
            if is_long and ext_data.get('extended_down', False):
                agreement_count += 1
                weighted_agreement += tf_weight
            elif not is_long and ext_data.get('extended_up', False):
                agreement_count += 1
                weighted_agreement += tf_weight
        
        # Calculate agreement ratio
        total_timeframes = len(extensions_by_timeframe)
        agreement_ratio = agreement_count / total_timeframes if total_timeframes > 0 else 0
        
        # Normalize weighted agreement
        weighted_agreement = weighted_agreement / total_weight if total_weight > 0 else 0
        
        return agreement_count, agreement_ratio, weighted_agreement
    
    def validate_signal_against_context(self, signal, extensions_by_timeframe):
        """
        Validate a signal against the multi-timeframe context
        
        Parameters:
        -----------
        signal : dict
            Signal information
        extensions_by_timeframe : dict
            Dictionary with extension data for each timeframe
            
        Returns:
        --------
        dict
            Validation result with confidence score
        """
        # Get signal timeframe and direction
        tf = signal['timeframe']
        direction = signal['direction']
        
        # Get timeframes in order of size
        all_timeframes = list(extensions_by_timeframe.keys())
        
        # Sort timeframes by duration (assuming timeframe names can be converted to minutes)
        try:
            tf_minutes = {t: self._parse_timeframe_minutes(t) for t in all_timeframes}
            sorted_timeframes = sorted(all_timeframes, key=lambda t: tf_minutes[t])
        except:
            # Fallback if parsing fails
            sorted_timeframes = all_timeframes
        
        # Find position of signal timeframe in hierarchy
        try:
            tf_idx = sorted_timeframes.index(tf)
        except ValueError:
            logger.warning(f"Signal timeframe {tf} not found in available timeframes")
            tf_idx = -1
        
        # Get higher and lower timeframes
        higher_tfs = sorted_timeframes[tf_idx+1:] if tf_idx >= 0 and tf_idx < len(sorted_timeframes) - 1 else []
        lower_tfs = sorted_timeframes[:tf_idx] if tf_idx > 0 else []
        
        # Check agreement with higher timeframes
        higher_agreement_count = 0
        higher_conflicts = 0
        
        for htf in higher_tfs:
            htf_data = extensions_by_timeframe.get(htf, {})
            
            # Check for agreement based on direction
            if direction == 'long':
                if htf_data.get('extended_down', False):
                    higher_agreement_count += 1
                elif htf_data.get('extended_up', False):
                    higher_conflicts += 1
            else:  # short
                if htf_data.get('extended_up', False):
                    higher_agreement_count += 1
                elif htf_data.get('extended_down', False):
                    higher_conflicts += 1
        
        # Calculate overall agreement across all timeframes
        agreement_count, agreement_ratio, weighted_agreement = self.check_timeframe_agreement(
            extensions_by_timeframe, direction
        )
        
        # Set confidence based on agreement
        confidence = 'low'
        if weighted_agreement >= 0.7:
            confidence = 'high'
        elif weighted_agreement >= 0.5:
            confidence = 'medium'
        
        # Check if minimum agreement met
        valid = agreement_count >= self.minimum_agreement
        
        # Adjust validity if prioritizing higher timeframes and there are conflicts
        if self.prioritize_higher_timeframe and higher_conflicts > higher_agreement_count:
            valid = False
            confidence = 'very_low'
        
        # Prepare result
        result = {
            'valid': valid,
            'confidence': confidence,
            'agreement_count': agreement_count,
            'agreement_ratio': agreement_ratio,
            'weighted_agreement': weighted_agreement,
            'higher_tf_agreement': higher_agreement_count,
            'higher_tf_conflicts': higher_conflicts,
            'signal_tf_position': tf_idx,
            'higher_timeframes': higher_tfs,
            'lower_timeframes': lower_tfs
        }
        
        return result
    
    def detect_trend_break(self, data, ema_period=9, lookback=5):
        """
        Detect potential trend break in a timeframe
        
        Parameters:
        -----------
        data : pandas.DataFrame
            Price data with OHLCV columns
        ema_period : int
            EMA period to use
        lookback : int
            Number of bars to look back
            
        Returns:
        --------
        dict
            Trend break analysis result
        """
        # Ensure we have enough data
        if len(data) < lookback + ema_period:
            return {'trend_breaking': False, 'reason': 'Insufficient data'}
        
        # Get recent section of data
        recent_data = data.iloc[-lookback:].copy()
        
        # Check if EMA is already calculated
        ema_col = f'EMA_{ema_period}'
        if ema_col not in recent_data.columns:
            # Calculate EMA
            try:
                import talib
                full_ema = pd.Series(talib.EMA(data['Close'].values, timeperiod=ema_period))
                recent_ema = full_ema.iloc[-lookback:].values
            except ImportError:
                import pandas_ta as ta
                full_ema = ta.ema(data['Close'], length=ema_period)
                recent_ema = full_ema.iloc[-lookback:].values
        else:
            recent_ema = recent_data[ema_col].values
        
        # Determine if price was consistently above or below EMA
        above_ema = recent_data['Close'].values > recent_ema
        below_ema = recent_data['Close'].values < recent_ema
        
        # Check for potential trend break
        was_uptrend = np.all(above_ema[:-3])  # Consistent uptrend in earlier bars
        was_downtrend = np.all(below_ema[:-3])  # Consistent downtrend in earlier bars
        
        recent_cross_down = was_uptrend and below_ema[-1]
        recent_cross_up = was_downtrend and above_ema[-1]
        
        trend_breaking = recent_cross_down or recent_cross_up
        
        # Return analysis
        return {
            'trend_breaking': trend_breaking,
            'recent_cross_down': recent_cross_down,
            'recent_cross_up': recent_cross_up,
            'was_uptrend': was_uptrend,
            'was_downtrend': was_downtrend
        }
    
    def _parse_timeframe_minutes(self, timeframe):
        """
        Parse timeframe string to get minutes
        
        Parameters:
        -----------
        timeframe : str
            Timeframe string (e.g., '1m', '1h', '1d')
            
        Returns:
        --------
        int
            Minutes represented by the timeframe
        """
        try:
            # Handle standard formats
            if timeframe.endswith('m'):
                return int(timeframe[:-1])
            elif timeframe.endswith('h'):
                return int(timeframe[:-1]) * 60
            elif timeframe.endswith('d'):
                return int(timeframe[:-1]) * 60 * 24
            elif timeframe.endswith('w'):
                return int(timeframe[:-1]) * 60 * 24 * 7
            else:
                # Try to parse as integer
                return int(timeframe)
        except (ValueError, AttributeError):
            # Default to zero if parsing fails
            logger.warning(f"Could not parse timeframe: {timeframe}")
            return 0

def resolve_timeframe_conflict(higher_tf_data, lower_tf_data):
    """
    Resolve conflict between two timeframes
    
    Parameters:
    -----------
    higher_tf_data : dict
        Data for higher timeframe with extension info
    lower_tf_data : dict
        Data for lower timeframe with extension info
        
    Returns:
    --------
    str
        Conflict resolution type
    """
    resolver = ConflictResolver()
    return resolver.detect_conflict(higher_tf_data, lower_tf_data)

def validate_signal_context(signal, extensions_by_timeframe):
    """
    Validate a signal against multi-timeframe context
    
    Parameters:
    -----------
    signal : dict
        Signal information
    extensions_by_timeframe : dict
        Dictionary with extension data for each timeframe
        
    Returns:
    --------
    dict
        Validation result
    """
    resolver = ConflictResolver()
    return resolver.validate_signal_against_context(signal, extensions_by_timeframe) 