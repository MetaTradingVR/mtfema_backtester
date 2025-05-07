"""
PaperFeet Laguerre RSI Indicator with Color Transitions

This is a custom implementation of the Laguerre RSI indicator with color-coding
for identifying momentum shifts and transitions.
"""

import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

def calculate_laguerre_rsi(data, gamma=0.7, period=4, column='Close'):
    """
    Calculate the Laguerre RSI indicator with PaperFeet color transitions.

    Timestamp: 2025-05-06 PST
    Reference: See 'PaperFeet Laguerre RSI' and 'PaperFeet Color Transition Verification' in strategy_playbook.md (Sections 2.1, 3.4)

    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLCV columns.
    gamma : float
        Gamma parameter that controls the smoothness (0-1).
    period : int
        Lookback period for smoothing.
    column : str
        Column name to use for calculation.

    Returns:
    --------
    pandas.DataFrame
        DataFrame with columns:
        - LRSI: Laguerre RSI value (0-1)
        - Color: 0=Red, 1=Yellow, 2=Green
        - BullishTransition, BearishTransition: bool flags
        - CompleteBullishTransition, CompleteBearishTransition: bool flags

    Usage Example:
    --------------
    >>> pf = calculate_laguerre_rsi(data)
    >>> if pf['CompleteBullishTransition'].iloc[-1]:
    ...     print('Bullish PaperFeet transition detected!')

    Edge Cases:
    -----------
    - Returns empty DataFrame if input is empty or None.
    - Handles division by zero in RSI calculation.
    - All logic branches should be unit tested (see tests/indicators/test_paperfeet.py).
    """
    if data is None or data.empty:
        logging.warning("Empty data provided for Laguerre RSI calculation")
        return pd.DataFrame()
    
    try:
        # Initialize values
        price = data[column].values
        L0 = np.zeros(len(price))
        L1 = np.zeros(len(price))
        L2 = np.zeros(len(price))
        L3 = np.zeros(len(price))
        
        # Calculate the Laguerre RSI
        for i in range(1, len(price)):
            L0[i] = (1 - gamma) * price[i] + gamma * L0[i-1]
            L1[i] = -gamma * L0[i] + L0[i-1] + gamma * L1[i-1]
            L2[i] = -gamma * L1[i] + L1[i-1] + gamma * L2[i-1]
            L3[i] = -gamma * L2[i] + L2[i-1] + gamma * L3[i-1]
        
        # Calculate RSI from the Laguerre filter
        cu = np.zeros(len(price))
        cd = np.zeros(len(price))
        
        for i in range(1, len(price)):
            if L0[i] >= L1[i]:
                cu[i] = L0[i] - L1[i]
            else:
                cd[i] = L1[i] - L0[i]
                
            if L1[i] >= L2[i]:
                cu[i] += L1[i] - L2[i]
            else:
                cd[i] += L2[i] - L1[i]
                
            if L2[i] >= L3[i]:
                cu[i] += L2[i] - L3[i]
            else:
                cd[i] += L3[i] - L2[i]
        
        # Smooth the cu and cd values
        smooth_cu = np.zeros(len(price))
        smooth_cd = np.zeros(len(price))
        
        for i in range(period, len(price)):
            smooth_cu[i] = np.sum(cu[i-period+1:i+1]) / period
            smooth_cd[i] = np.sum(cd[i-period+1:i+1]) / period
        
        # Calculate RSI
        lrsi = np.zeros(len(price))
        for i in range(period, len(price)):
            if smooth_cu[i] + smooth_cd[i] != 0:
                lrsi[i] = smooth_cu[i] / (smooth_cu[i] + smooth_cd[i])
            else:
                lrsi[i] = 0.5  # Default value when division by zero
        
        # Create result DataFrame
        result = pd.DataFrame(index=data.index)
        result['LRSI'] = lrsi
        
        # Add color indicator (0=red, 1=yellow, 2=green)
        result['Color'] = 1  # Default to yellow (transition)
        
        # Assign colors based on RSI values and transitions
        # Red: Bearish momentum/oversold (0-0.3)
        # Yellow: Transitional state (0.3-0.7)
        # Green: Bullish momentum/overbought (0.7-1.0)
        result.loc[result['LRSI'] <= 0.3, 'Color'] = 0  # Red
        result.loc[result['LRSI'] >= 0.7, 'Color'] = 2  # Green
        
        # Add trend detection (0=down, 1=neutral, 2=up)
        result['Trend'] = 1  # Default to neutral
        
        # Detect color transitions
        transitions = pd.DataFrame(index=data.index)
        transitions['RedToYellow'] = False
        transitions['YellowToGreen'] = False
        transitions['GreenToYellow'] = False
        transitions['YellowToRed'] = False
        
        # Identify transitions
        for i in range(1, len(result)):
            prev_color = result['Color'].iloc[i-1]
            curr_color = result['Color'].iloc[i]
            
            if prev_color == 0 and curr_color == 1:
                transitions['RedToYellow'].iloc[i] = True
            elif prev_color == 1 and curr_color == 2:
                transitions['YellowToGreen'].iloc[i] = True
            elif prev_color == 2 and curr_color == 1:
                transitions['GreenToYellow'].iloc[i] = True
            elif prev_color == 1 and curr_color == 0:
                transitions['YellowToRed'].iloc[i] = True
        
        # Detect bullish and bearish transitions
        result['BullishTransition'] = transitions['RedToYellow'] | transitions['YellowToGreen']
        result['BearishTransition'] = transitions['GreenToYellow'] | transitions['YellowToRed']
        
        # Complete trend transition (Red->Yellow->Green or Green->Yellow->Red)
        result['CompleteBullishTransition'] = False
        result['CompleteBearishTransition'] = False
        
        # Look for complete transitions (requires 3 bars)
        for i in range(2, len(result)):
            # Complete bullish transition: Red -> Yellow -> Green
            if (result['Color'].iloc[i-2] == 0 and 
                result['Color'].iloc[i-1] == 1 and 
                result['Color'].iloc[i] == 2):
                result['CompleteBullishTransition'].iloc[i] = True
            
            # Complete bearish transition: Green -> Yellow -> Red
            if (result['Color'].iloc[i-2] == 2 and 
                result['Color'].iloc[i-1] == 1 and 
                result['Color'].iloc[i] == 0):
                result['CompleteBearishTransition'].iloc[i] = True
        
        logger.info(f"Calculated Laguerre RSI with gamma={gamma} successfully")
        return result
    
    except Exception as e:
        logger.error(f"Error calculating Laguerre RSI: {str(e)}")
        return pd.DataFrame()

def validate_paperfeet_transition(data, lookback=3, direction="bullish"):
    """
    Validate if a PaperFeet color transition has occurred in the specified direction.

    Timestamp: 2025-05-06 PST
    Reference: See 'PaperFeet Color Transition Verification' in strategy_playbook.md (Section 3.4)

    Parameters:
    -----------
    data : pandas.DataFrame
        DataFrame with PaperFeet Color column.
    lookback : int
        Number of bars to look back.
    direction : str
        "bullish" or "bearish" to specify the transition direction.

    Returns:
    --------
    bool
        True if the specified transition is detected.

    Usage Example:
    --------------
    >>> pf = calculate_laguerre_rsi(data)
    >>> if validate_paperfeet_transition(pf, lookback=3, direction="bullish"):
    ...     print('Bullish transition detected!')

    Edge Cases:
    -----------
    - Returns False if not enough data for lookback.
    - Returns False for unknown direction.
    """
    if len(data) < lookback:
        return False
    
    # Get the last N colors
    last_colors = data['Color'].iloc[-lookback:].values
    
    if direction.lower() == "bullish":
        # Check for Red -> Yellow -> Green transition
        return (last_colors[0] == 0 and 
                last_colors[1] == 1 and 
                last_colors[2] == 2)
    elif direction.lower() == "bearish":
        # Check for Green -> Yellow -> Red transition
        return (last_colors[0] == 2 and 
                last_colors[1] == 1 and 
                last_colors[2] == 0)
    else:
        logger.warning(f"Unknown transition direction: {direction}")
        return False

def is_paperfeet_transitioning(data, current_index, direction):
    """
    Check if PaperFeet indicator is showing a color transition at the specified index
    
    Parameters:
    -----------
    data : pandas.DataFrame
        DataFrame with PaperFeet indicator data
    current_index : int
        Current index to check for transition
    direction : str
        Direction of the transition ('long' or 'short')
        
    Returns:
    --------
    dict
        Transition validation results
    """
    if 'Color' not in data.columns:
        logger.warning("PaperFeet Color column not found in data")
        return {
            'valid': False,
            'reason': 'PaperFeet data not available',
            'has_color_data': False
        }
    
    # Need at least 3 bars for a full transition
    if current_index < 2:
        return {
            'valid': False,
            'reason': 'Insufficient bars for transition detection',
            'has_color_data': True
        }
    
    try:
        # Get the last 3 color values
        colors = []
        for i in range(3):
            idx = current_index - 2 + i
            if 0 <= idx < len(data):
                colors.append(data['Color'].iloc[idx])
            else:
                colors.append(None)
        
        # Check for valid colors
        if None in colors:
            return {
                'valid': False,
                'reason': 'Missing color data',
                'has_color_data': True,
                'colors': colors
            }
        
        if direction == 'long':
            # For long trades, look for Red -> Yellow -> Green
            valid = (colors[0] == 0 and colors[1] == 1 and colors[2] == 2)
            reason = 'Complete bullish transition' if valid else 'No bullish transition detected'
            
            return {
                'valid': valid,
                'reason': reason,
                'colors': colors,
                'has_color_data': True,
                'transition_type': 'bullish' if valid else None
            }
        
        elif direction == 'short':
            # For short trades, look for Green -> Yellow -> Red
            valid = (colors[0] == 2 and colors[1] == 1 and colors[2] == 0)
            reason = 'Complete bearish transition' if valid else 'No bearish transition detected'
            
            return {
                'valid': valid,
                'reason': reason,
                'colors': colors,
                'has_color_data': True,
                'transition_type': 'bearish' if valid else None
            }
        
        else:
            return {
                'valid': False,
                'reason': f'Unknown direction: {direction}',
                'has_color_data': True,
                'colors': colors
            }
    
    except Exception as e:
        logger.error(f"Error checking PaperFeet transition: {str(e)}")
        return {
            'valid': False,
            'reason': f'Error: {str(e)}',
            'has_color_data': True
        }

def calculate_paperfeet_rsi(data, gamma=0.7, period=4, column='Close'):
    """
    Calculate the PaperFeet Laguerre RSI indicator
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Price data with OHLCV columns
    gamma : float
        Gamma parameter that controls the smoothness (0-1)
    period : int
        Lookback period for smoothing
    column : str
        Column name to use for calculation
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with PaperFeet indicator values
    """
    # Calculate using the Laguerre RSI function
    return calculate_laguerre_rsi(data, gamma, period, column)
