"""
Signal generation module for the MT 9 EMA Extension Strategy.

This module contains functions for generating trading signals based on
EMA extensions and reclamations across multiple timeframes.
"""

import pandas as pd
import numpy as np
import logging

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
        # Get data for this timeframe
        data = timeframe_data.get_timeframe(tf)
        if data is None or data.empty:
            logger.warning(f"No data available for timeframe {tf}")
            continue
            
        # Get extension threshold for this timeframe
        extension_threshold = params.get_extension_threshold(tf)
        
        # Find reclamation points (use Reclamation DataFrame directly)
        reclamation_data = timeframe_data.get_indicator(tf, "Reclamation")
        if reclamation_data is None or reclamation_data.empty:
            logger.info(f"No reclamation data available for timeframe {tf}")
            continue
            
        extension_data = timeframe_data.get_indicator(tf, "Extension")
        if extension_data is None or extension_data.empty:
            logger.info(f"No extension data available for timeframe {tf}")
            continue
            
        # Process bullish reclamations
        if 'BullishReclaim' in reclamation_data.columns:
            bullish_reclaims = reclamation_data[reclamation_data['BullishReclaim']].index
            for idx in bullish_reclaims:
                try:
                    # Get price data at reclamation point
                    price_data = data.loc[idx]
                    
                    # Verify extension condition
                    extension_pct = extension_data.loc[idx]
                    if hasattr(extension_pct, 'iloc'):
                        extension_pct = extension_pct.iloc[0]
                        
                    if extension_pct < extension_threshold:
                        logger.debug(f"Skipping bullish signal at {idx} due to insufficient extension: {extension_pct} < {extension_threshold}")
                        continue
                        
                    # Find recent swing low for stop placement
                    n_bars_back = params.get_param('risk_management.lookback_bars', 5)
                    try:
                        lookback_idx = max(0, data.index.get_loc(idx) - n_bars_back)
                        lookback_data = data.iloc[lookback_idx:data.index.get_loc(idx)]
                        stop_price = lookback_data['Low'].min() * 0.99  # Add 1% buffer
                    except Exception as e:
                        logger.warning(f"Error finding stop price: {str(e)}. Using default stop.")
                        # Fallback to a default stop percentage
                        stop_pct = params.get_param('risk_management.default_stop_percent', 0.01)
                        stop_price = price_data['Close'] * (1 - stop_pct)
                    
                    # Check if PaperFeet confirmation is required
                    use_paperfeet = params.get_param('indicators.use_paperfeet_confirmation', False)
                    paperfeet_ok = True
                    
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
                        'entry_price': float(price_data['Close']),
                        'stop_price': float(stop_price),
                        'extension_pct': float(extension_pct),
                        'reclamation_bar': True,
                        'confidence': calculate_signal_confidence(extension_pct, extension_threshold, tf)
                    }
                    
                    signals.append(signal)
                    logger.info(f"Generated LONG signal at {idx} on {tf} timeframe with extension {extension_pct:.2%}")
                    
                except (KeyError, IndexError, ValueError) as e:
                    logger.warning(f"Error generating bullish signal at {idx}: {str(e)}")
        
        # Process bearish reclamations
        if 'BearishReclaim' in reclamation_data.columns:
            bearish_reclaims = reclamation_data[reclamation_data['BearishReclaim']].index
            for idx in bearish_reclaims:
                try:
                    # Get price data at reclamation point
                    price_data = data.loc[idx]
                    
                    # Verify extension condition
                    extension_pct = extension_data.loc[idx]
                    if hasattr(extension_pct, 'iloc'):
                        extension_pct = extension_pct.iloc[0]
                        
                    if extension_pct < extension_threshold:
                        logger.debug(f"Skipping bearish signal at {idx} due to insufficient extension: {extension_pct} < {extension_threshold}")
                        continue
                        
                    # Find recent swing high for stop placement
                    n_bars_back = params.get_param('risk_management.lookback_bars', 5)
                    try:
                        lookback_idx = max(0, data.index.get_loc(idx) - n_bars_back)
                        lookback_data = data.iloc[lookback_idx:data.index.get_loc(idx)]
                        stop_price = lookback_data['High'].max() * 1.01  # Add 1% buffer
                    except Exception as e:
                        logger.warning(f"Error finding stop price: {str(e)}. Using default stop.")
                        # Fallback to a default stop percentage
                        stop_pct = params.get_param('risk_management.default_stop_percent', 0.01)
                        stop_price = price_data['Close'] * (1 + stop_pct)
                    
                    # Check if PaperFeet confirmation is required
                    use_paperfeet = params.get_param('indicators.use_paperfeet_confirmation', False)
                    paperfeet_ok = True
                    
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
                        'entry_price': float(price_data['Close']),
                        'stop_price': float(stop_price),
                        'extension_pct': float(extension_pct),
                        'reclamation_bar': True,
                        'confidence': calculate_signal_confidence(extension_pct, extension_threshold, tf)
                    }
                    
                    signals.append(signal)
                    logger.info(f"Generated SHORT signal at {idx} on {tf} timeframe with extension {extension_pct:.2%}")
                    
                except (KeyError, IndexError, ValueError) as e:
                    logger.warning(f"Error generating bearish signal at {idx}: {str(e)}")
    
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