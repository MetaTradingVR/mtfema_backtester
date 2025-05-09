"""
Signal generation module for the MT 9 EMA Extension Strategy.

This module contains functions for generating trading signals based on
EMA extensions and reclamations across multiple timeframes.
"""

import pandas as pd
import numpy as np
import logging

from mtfema_backtester.indicators.fibonacci_targets import calculate_fib_targets

logger = logging.getLogger(__name__)

def generate_signals(timeframe_data, params=None):
    """Generate trading signals based on EMA extensions and reclamations.
    
    Args:
        timeframe_data: TimeframeData instance with indicators
        params: Strategy parameters
        
    Returns:
        pandas.DataFrame: DataFrame with trading signals
    """
    if params is None:
        from mtfema_backtester.config import STRATEGY_PARAMS
        params = STRATEGY_PARAMS
        
    signals = []
    
    # Process each timeframe
    for tf in timeframe_data.get_available_timeframes():
        try:
            # Skip timeframes without all required data
            if not timeframe_data.has_price_data(tf) or not timeframe_data.has_indicator(tf, "EMA_9"):
                logger.warning(f"Skipping {tf} timeframe due to missing data")
                continue
                
            # Get price data and indicators for this timeframe
            price_data = timeframe_data.get_price_data(tf)
            ema_9 = timeframe_data.get_indicator(tf, "EMA_9")
            
            # Skip timeframes with insufficient data
            if len(price_data) < 20 or len(ema_9) < 20:
                logger.warning(f"Skipping {tf} timeframe due to insufficient data points")
                continue
                
            # Get extension threshold for this timeframe
            extension_threshold = params['ema']['extension_thresholds'].get(
                tf, 1.0  # Default to 1.0% if not specified
            )
            
            # PaperFeet is optional and used for additional confirmation if available
            use_paperfeet = timeframe_data.has_indicator(tf, "PaperFeet")
                
            # Analyze each bar for signals
            for i in range(2, len(price_data)):
                # Skip weekends and holidays if daily timeframe
                if tf == "1d" and not is_trading_day(price_data.index[i]):
                    continue
                    
                idx = price_data.index[i]
                
                # Get current and previous values
                curr_close = price_data['Close'].iloc[i]
                curr_ema = ema_9.iloc[i]
                prev_close = price_data['Close'].iloc[i-1]
                prev_ema = ema_9.iloc[i-1]
                
                # Calculate the extension percentage from EMA
                extension_pct = abs(curr_close - curr_ema) / curr_ema * 100
                
                # Check for EMA reclamation on current bar after extension
                try:
                    # BULLISH reclamation - price moves from below EMA to above EMA
                    # after being extended below EMA by the threshold percentage
                    if (prev_close < prev_ema and                    # Previous bar closed below EMA
                        prev_close <= prev_ema * (1 - extension_threshold/100) and  # Previous close extended below EMA
                        curr_close > curr_ema):                     # Current bar closes above EMA
                        
                        # Set initial paperfeet confirmation to True (will be set to False if check fails)
                        paperfeet_ok = True
                        
                        # Calculate stop price (below recent swing low)
                        lookback = 10
                        lookback_section = price_data.iloc[max(0, i-lookback):i]
                        stop_price = lookback_section['Low'].min() * 0.999  # Just below recent low
                        
                        if use_paperfeet:
                            paperfeet_data = timeframe_data.get_indicator(tf, "PaperFeet")
                            if paperfeet_data is not None and not paperfeet_data.empty:
                                paperfeet_ok = validate_paperfeet_transition(paperfeet_data, idx, is_long=True)
                        
                        if not paperfeet_ok:
                            logger.debug(f"Skipping bullish signal at {idx} due to PaperFeet confirmation failure")
                            continue
                        
                        # Create the signal
                        signal = {
                            'datetime': idx,
                            'timeframe': tf,
                            'type': 'LONG',
                            'entry_price': float(price_data['Close'].iloc[i]),
                            'stop_price': float(stop_price),
                            'extension_pct': float(extension_pct),
                            'reclamation_bar': True,
                            'confidence': calculate_signal_confidence(extension_pct, extension_threshold, tf)
                        }
                        
                        # Add Fibonacci targets
                        signal_with_targets = calculate_fib_targets(signal, price_data.iloc[:i+1])
                        
                        signals.append(signal_with_targets)
                        logger.info(f"Generated LONG signal at {idx} on {tf} timeframe with extension {extension_pct:.2%}")
                        
                    # BEARISH reclamation - price moves from above EMA to below EMA
                    # after being extended above EMA by the threshold percentage
                    elif (prev_close > prev_ema and                  # Previous bar closed above EMA
                          prev_close >= prev_ema * (1 + extension_threshold/100) and  # Previous close extended above EMA
                          curr_close < curr_ema):                   # Current bar closes below EMA
                        
                        # Set initial paperfeet confirmation to True (will be set to False if check fails)
                        paperfeet_ok = True
                        
                        # Calculate stop price (above recent swing high)
                        lookback = 10
                        lookback_section = price_data.iloc[max(0, i-lookback):i]
                        stop_price = lookback_section['High'].max() * 1.001  # Just above recent high
                        
                        if use_paperfeet:
                            paperfeet_data = timeframe_data.get_indicator(tf, "PaperFeet")
                            if paperfeet_data is not None and not paperfeet_data.empty:
                                paperfeet_ok = validate_paperfeet_transition(paperfeet_data, idx, is_long=False)
                        
                        if not paperfeet_ok:
                            logger.debug(f"Skipping bearish signal at {idx} due to PaperFeet confirmation failure")
                            continue
                        
                        # Create the signal
                        signal = {
                            'datetime': idx,
                            'timeframe': tf,
                            'type': 'SHORT',
                            'entry_price': float(price_data['Close'].iloc[i]),
                            'stop_price': float(stop_price),
                            'extension_pct': float(extension_pct),
                            'reclamation_bar': True,
                            'confidence': calculate_signal_confidence(extension_pct, extension_threshold, tf)
                        }
                        
                        # Add Fibonacci targets
                        signal_with_targets = calculate_fib_targets(signal, price_data.iloc[:i+1])
                        
                        signals.append(signal_with_targets)
                        logger.info(f"Generated SHORT signal at {idx} on {tf} timeframe with extension {extension_pct:.2%}")
                        
                except (KeyError, IndexError, ValueError) as e:
                    logger.warning(f"Error generating signal at {idx}: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing timeframe {tf}: {str(e)}")
            continue
    
    if not signals:
        logger.warning("No trading signals generated")
        return pd.DataFrame()
    
    # Convert to DataFrame and sort by datetime
    signals_df = pd.DataFrame(signals)
    if not signals_df.empty:
        signals_df.sort_values('datetime', inplace=True)
    
    return signals_df

def validate_paperfeet_transition(paperfeet_data, idx, is_long=True, lookback=3):
    """
    Validate PaperFeet color transition for signal confirmation.
    
    For long signals: Looking for Red → Yellow → Green transition
    For short signals: Looking for Green → Yellow → Red transition
    
    Args:
        paperfeet_data: DataFrame with PaperFeet color data
        idx: Current index to validate
        is_long: Whether we're validating a long signal
        lookback: Number of bars to look back for transition
        
    Returns:
        bool: True if transition is valid, False otherwise
    """
    try:
        # Get position of current index
        pos = paperfeet_data.index.get_loc(idx)
        
        # Can't validate if we don't have enough history
        if pos < lookback:
            return False
            
        # Get colors for the last n bars (including current)
        # 0 = Red (bearish/oversold)
        # 1 = Yellow (transition)
        # 2 = Green (bullish/overbought)
        colors = []
        for i in range(lookback):
            color_value = paperfeet_data.iloc[pos - i].iloc[0]
            colors.insert(0, color_value)
        
        if is_long:
            # Looking for Red → Yellow → Green transition
            return colors[0] == 0 and colors[1] == 1 and colors[2] == 2
        else:
            # Looking for Green → Yellow → Red transition
            return colors[0] == 2 and colors[1] == 1 and colors[2] == 0
            
    except (KeyError, IndexError) as e:
        logger.warning(f"Error validating PaperFeet transition: {str(e)}")
        return False

def calculate_signal_confidence(extension_pct, threshold, timeframe):
    """
    Calculate signal confidence score based on extension percentage.
    
    Args:
        extension_pct: Extension percentage
        threshold: Threshold for the timeframe
        timeframe: Timeframe string
        
    Returns:
        float: Confidence score between 0 and 1
    """
    # Base confidence starts at 0.5
    confidence = 0.5
    
    # Add confidence based on how much extension exceeds threshold
    confidence += min(0.3, (extension_pct / threshold - 1) * 0.5)
    
    # Add confidence based on timeframe (higher timeframes get higher confidence)
    tf_minutes = get_timeframe_minutes(timeframe)
    if tf_minutes >= 1440:  # Daily or higher
        confidence += 0.2
    elif tf_minutes >= 240:  # 4h or higher
        confidence += 0.15
    elif tf_minutes >= 60:   # 1h or higher
        confidence += 0.1
    
    # Cap at 1.0
    return min(1.0, confidence)

def get_timeframe_minutes(timeframe):
    """
    Convert timeframe string to minutes.
    
    Args:
        timeframe: Timeframe string (e.g., '1d', '1h', '15m')
        
    Returns:
        int: Number of minutes in the timeframe
    """
    # Handle special case for 1
    if timeframe == '1':
        timeframe = '1d'  # Assume 1 means 1 day
    
    if timeframe.endswith('m'):
        try:
            return int(timeframe[:-1])
        except ValueError:
            logger.warning(f"Invalid minute timeframe format: {timeframe}")
            return 1440  # Default to daily
        
    elif timeframe.endswith('h'):
        try:
            return int(timeframe[:-1]) * 60
        except ValueError:
            logger.warning(f"Invalid hour timeframe format: {timeframe}")
            return 1440  # Default to daily
        
    elif timeframe.endswith('d'):
        try:
            return int(timeframe[:-1]) * 1440
        except ValueError:
            logger.warning(f"Invalid day timeframe format: {timeframe}")
            return 1440  # Default to daily
        
    elif timeframe.endswith('w'):
        try:
            return int(timeframe[:-1]) * 1440 * 7
        except ValueError:
            logger.warning(f"Invalid week timeframe format: {timeframe}")
            return 1440 * 7  # Default to weekly
    
    logger.warning(f"Unknown timeframe format: {timeframe}, defaulting to daily")
    return 1440  # Default to daily 