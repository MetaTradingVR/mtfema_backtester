"""
Signal Generator for the Multi-Timeframe 9 EMA Extension Strategy.

This module integrates all strategy components (extension detection, reclamation detection,
pullback validation, conflict resolution, and target management) to generate trade signals.
"""

import logging
import pandas as pd
import numpy as np

from mtfema_backtester.strategy.extension_detector import detect_extensions
from mtfema_backtester.strategy.reclamation_detector import ReclamationDetector
from mtfema_backtester.strategy.pullback_validator import validate_pullback
from mtfema_backtester.strategy.conflict_resolver import ConflictResolver, validate_signal_context
from mtfema_backtester.strategy.target_manager import get_target_for_signal
from mtfema_backtester.indicators.paperfeet import is_paperfeet_transitioning

logger = logging.getLogger(__name__)

class SignalGenerator:
    """
    Generates trading signals by integrating all strategy components.
    """
    
    def __init__(self, timeframe_data, ema_period=9):
        """
        Initialize the SignalGenerator
        
        Parameters:
        -----------
        timeframe_data : TimeframeData
            Multi-timeframe data
        ema_period : int
            EMA period to use for strategy calculations (default: 9)
        """
        self.timeframe_data = timeframe_data
        self.conflict_resolver = ConflictResolver()
        self.ema_period = ema_period
        
        # Get available timeframes sorted by timeframe minutes
        self.timeframes = self.timeframe_data.get_available_timeframes()
        tf_minutes = {
            tf: self.timeframe_data.get_timeframe_minutes(tf) 
            for tf in self.timeframes
        }
        self.sorted_timeframes = sorted(self.timeframes, key=lambda tf: tf_minutes[tf])
        
        logger.info(f"SignalGenerator initialized with timeframes: {self.sorted_timeframes}")
    
    def detect_extensions_for_all_timeframes(self):
        """
        Detect price extensions across all timeframes
        
        Returns:
        --------
        dict
            Dictionary with extension data for each timeframe
        """
        extensions = {}
        
        for tf in self.timeframes:
            # Get timeframe data
            tf_data = self.timeframe_data.get_timeframe(tf)
            
            # Detect extensions
            ext_data = detect_extensions(tf_data, tf)
            
            # Store extension data
            extensions[tf] = ext_data
            
            logger.debug(f"Extensions for {tf}: {ext_data}")
        
        return extensions
    
    def detect_reclamations_for_all_timeframes(self):
        """
        Detect price reclamations of the EMA for all timeframes
        
        Returns:
        --------
        dict
            Dictionary with timeframes as keys and reclamation DataFrames as values
        """
        reclamation_data = {}
        
        for tf in self.timeframe_data.get_available_timeframes():
            logger.info(f"Detecting reclamations for {tf} timeframe")
            tf_data = self.timeframe_data.get_timeframe(tf)
            ema_data = self.timeframe_data.get_indicator(tf, f"EMA_{self.ema_period}")
            
            if tf_data is not None and not tf_data.empty:
                # Use ReclamationDetector class
                detector = ReclamationDetector(ema_period=self.ema_period)
                recl_data = detector.detect_reclamation(tf_data, ema=ema_data)
                
                if not recl_data.empty:
                    reclamation_data[tf] = recl_data
                    logger.info(f"Detected reclamations for {tf} timeframe")
        
        return reclamation_data
    
    def validate_signals(self, reclamations, extensions):
        """
        Validate potential signals from reclamations against extensions
        
        Parameters:
        -----------
        reclamations : dict
            Dictionary with reclamation data for each timeframe
        extensions : dict
            Dictionary with extension data for each timeframe
            
        Returns:
        --------
        list
            List of validated signals
        """
        validated_signals = []
        
        # Check each timeframe for reclamations
        for tf in self.timeframes:
            tf_recl = reclamations.get(tf, {})
            
            # Check for bullish reclamation (for long trade)
            if tf_recl.get('reclaimed_up', False):
                # Create potential signal
                signal = {
                    'timeframe': tf,
                    'direction': 'long',
                    'reclamation_data': tf_recl,
                    'time': tf_recl.get('reclamation_time', None),
                    'price': tf_recl.get('reclamation_price', None),
                    'index': tf_recl.get('reclamation_index', None)
                }
                
                # Validate against multi-timeframe context
                context_validation = validate_signal_context(signal, extensions)
                signal.update(context_validation)
                
                # Only proceed if valid context
                if context_validation['valid']:
                    # Validate pullback
                    tf_data = self.timeframe_data.get_timeframe(tf)
                    ema_col = 'EMA_9'
                    ema_series = tf_data[ema_col] if ema_col in tf_data.columns else None
                    
                    pullback_validation = validate_pullback(
                        tf_data, tf_recl, 'long', ema_series
                    )
                    
                    signal['pullback_validation'] = pullback_validation
                    
                    # Check PaperFeet transition
                    if 'PaperFeet' in tf_data.columns:
                        paperfeet_transition = is_paperfeet_transitioning(
                            tf_data, signal['index'], 'long'
                        )
                        signal['paperfeet_transition'] = paperfeet_transition
                    else:
                        signal['paperfeet_transition'] = None
                    
                    # Get target
                    target = get_target_for_signal(
                        self.timeframe_data, signal, self.sorted_timeframes
                    )
                    signal['target'] = target
                    
                    # Add to validated signals if pullback is valid
                    if pullback_validation.get('valid', False):
                        signal['valid'] = True
                        validated_signals.append(signal)
                    else:
                        signal['valid'] = False
                        logger.debug(f"Signal rejected due to invalid pullback: {pullback_validation}")
            
            # Check for bearish reclamation (for short trade)
            if tf_recl.get('reclaimed_down', False):
                # Create potential signal
                signal = {
                    'timeframe': tf,
                    'direction': 'short',
                    'reclamation_data': tf_recl,
                    'time': tf_recl.get('reclamation_time', None),
                    'price': tf_recl.get('reclamation_price', None),
                    'index': tf_recl.get('reclamation_index', None)
                }
                
                # Validate against multi-timeframe context
                context_validation = validate_signal_context(signal, extensions)
                signal.update(context_validation)
                
                # Only proceed if valid context
                if context_validation['valid']:
                    # Validate pullback
                    tf_data = self.timeframe_data.get_timeframe(tf)
                    ema_col = 'EMA_9'
                    ema_series = tf_data[ema_col] if ema_col in tf_data.columns else None
                    
                    pullback_validation = validate_pullback(
                        tf_data, tf_recl, 'short', ema_series
                    )
                    
                    signal['pullback_validation'] = pullback_validation
                    
                    # Check PaperFeet transition
                    if 'PaperFeet' in tf_data.columns:
                        paperfeet_transition = is_paperfeet_transitioning(
                            tf_data, signal['index'], 'short'
                        )
                        signal['paperfeet_transition'] = paperfeet_transition
                    else:
                        signal['paperfeet_transition'] = None
                    
                    # Get target
                    target = get_target_for_signal(
                        self.timeframe_data, signal, self.sorted_timeframes
                    )
                    signal['target'] = target
                    
                    # Add to validated signals if pullback is valid
                    if pullback_validation.get('valid', False):
                        signal['valid'] = True
                        validated_signals.append(signal)
                    else:
                        signal['valid'] = False
                        logger.debug(f"Signal rejected due to invalid pullback: {pullback_validation}")
        
        return validated_signals
    
    def generate_signals(self):
        """
        Generate trading signals based on the Multi-Timeframe 9 EMA Extension Strategy
        
        Returns:
        --------
        list
            List of validated trading signals
        """
        # Step 1: Detect extensions across all timeframes
        extensions = self.detect_extensions_for_all_timeframes()
        
        # Step 2: Detect reclamations across all timeframes
        reclamations = self.detect_reclamations_for_all_timeframes()
        
        # Step 3: Validate signals
        signals = self.validate_signals(reclamations, extensions)
        
        # Log results
        logger.info(f"Generated {len(signals)} valid signals")
        for signal in signals:
            logger.info(f"Signal: {signal['direction']} on {signal['timeframe']} with confidence {signal['confidence']}")
        
        return signals

def generate_signals(timeframe_data, ema_period=9):
    """
    Generate signals using the SignalGenerator
    
    Parameters:
    -----------
    timeframe_data : TimeframeData
        Multi-timeframe data
    ema_period : int
        EMA period to use for strategy calculations (default: 9)
        
    Returns:
    --------
    dict
        Dictionary with signal information
    """
    generator = SignalGenerator(timeframe_data, ema_period)
    return generator.generate_signals() 