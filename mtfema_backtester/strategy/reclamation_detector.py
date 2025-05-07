"""
Module for detecting 9 EMA reclamations and tracking the details of those reclamations
"""

import pandas as pd
import numpy as np
import logging
from mtfema_backtester.config import STRATEGY_PARAMS

logger = logging.getLogger(__name__)

class ReclamationDetector:
    """
    Class for detecting when price reclaims the 9 EMA
    and tracking the details needed for pullback analysis
    """
    
    def __init__(self, ema_period=9, confirmation_bars=None):
        """
        Initialize the ReclamationDetector
        
        Parameters:
        -----------
        ema_period : int
            Period for the EMA calculation
        confirmation_bars : int, optional
            Number of bars needed to confirm an EMA reclamation
        """
        self.ema_period = ema_period
        
        # Use config value if not provided
        if confirmation_bars is None:
            self.confirmation_bars = STRATEGY_PARAMS['ema']['reclamation_confirmation_bars']
        else:
            self.confirmation_bars = confirmation_bars
            
        # Store reclamation details for later analysis
        self.reclamation_details = {
            'bullish': [],  # Bullish reclamations (price moves above EMA)
            'bearish': []   # Bearish reclamations (price moves below EMA)
        }
        
        logger.info(f"ReclamationDetector initialized with EMA period {ema_period} "
                   f"and confirmation bars {self.confirmation_bars}")
    
    def detect_reclamation(self, data, ema=None, price_col='Close'):
        """
        Detect when price reclaims the EMA
        
        Parameters:
        -----------
        data : pandas.DataFrame
            Price data with OHLCV columns
        ema : pandas.Series, optional
            Pre-calculated EMA values
        price_col : str
            Column name for price data
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with reclamation signals
        """
        if data is None or len(data) < 2:
            logger.warning("Insufficient data for reclamation detection")
            return pd.DataFrame()
        
        try:
            # Calculate EMA if not provided
            if ema is None:
                # Try to import TA-Lib first, fall back to pandas-ta
                try:
                    import talib
                    ema = pd.Series(
                        talib.EMA(data[price_col].values, timeperiod=self.ema_period),
                        index=data.index
                    )
                except ImportError:
                    import pandas_ta as ta
                    ema = ta.ema(data[price_col], length=self.ema_period)
            
            # Check if data is aligned with EMA
            if len(data) != len(ema):
                logger.warning(f"Data and EMA length mismatch: {len(data)} vs {len(ema)}")
                # Align the data
                ema = ema.reindex(data.index, method='ffill')
            
            # Create result DataFrame
            result = pd.DataFrame(index=data.index)
            result['EMA'] = ema
            
            # Initialize signal arrays
            bullish_reclaim = np.zeros(len(data), dtype=bool)
            bearish_reclaim = np.zeros(len(data), dtype=bool)
            
            # Find crossovers
            for i in range(1, len(data)):
                # Skip if we can't safely access the indices
                if i-1 >= len(data) or i >= len(data) or i-1 >= len(ema) or i >= len(ema):
                    continue
                
                # Get the current and previous values
                prev_price = data[price_col].iloc[i-1]
                curr_price = data[price_col].iloc[i]
                prev_ema = ema.iloc[i-1]
                curr_ema = ema.iloc[i]
                
                # Handle Series by getting scalar values
                if isinstance(prev_price, pd.Series):
                    prev_price = prev_price.iloc[0]
                if isinstance(curr_price, pd.Series):
                    curr_price = curr_price.iloc[0]
                if isinstance(prev_ema, pd.Series):
                    prev_ema = prev_ema.iloc[0]
                if isinstance(curr_ema, pd.Series):
                    curr_ema = curr_ema.iloc[0]
                
                # Bullish reclamation (close crosses above EMA)
                if prev_price < prev_ema and curr_price > curr_ema:
                    bullish_reclaim[i] = True
                    
                    # Record the reclamation details
                    reclaim_details = {
                        'index': i,
                        'time': data.index[i],
                        'reclaim_price': curr_price,
                        'reclaim_ema': curr_ema,
                        'reclaim_high': float(data['High'].iloc[i].iloc[0]) if isinstance(data['High'].iloc[i], pd.Series) else float(data['High'].iloc[i]),
                        'reclaim_low': float(data['Low'].iloc[i].iloc[0]) if isinstance(data['Low'].iloc[i], pd.Series) else float(data['Low'].iloc[i]),
                        'confirmed': False,
                        'confirmation_index': None,
                        'pullback_detected': False,
                        'pullback_price': None,
                        'pullback_index': None
                    }
                    
                    self.reclamation_details['bullish'].append(reclaim_details)
                
                # Bearish reclamation (close crosses below EMA)
                elif prev_price > prev_ema and curr_price < curr_ema:
                    bearish_reclaim[i] = True
                    
                    # Record the reclamation details
                    reclaim_details = {
                        'index': i,
                        'time': data.index[i],
                        'reclaim_price': curr_price,
                        'reclaim_ema': curr_ema,
                        'reclaim_high': float(data['High'].iloc[i].iloc[0]) if isinstance(data['High'].iloc[i], pd.Series) else float(data['High'].iloc[i]),
                        'reclaim_low': float(data['Low'].iloc[i].iloc[0]) if isinstance(data['Low'].iloc[i], pd.Series) else float(data['Low'].iloc[i]),
                        'confirmed': False,
                        'confirmation_index': None,
                        'pullback_detected': False,
                        'pullback_price': None,
                        'pullback_index': None
                    }
                    
                    self.reclamation_details['bearish'].append(reclaim_details)
            
            # Add signals to result
            result['BullishReclaim'] = bullish_reclaim
            result['BearishReclaim'] = bearish_reclaim
            
            # Add confirmation tracking if confirmation bars > 0
            if self.confirmation_bars > 0:
                result = self._track_confirmation(data, result, ema, price_col)
            
            logger.info(f"Detected {bullish_reclaim.sum()} bullish and "
                       f"{bearish_reclaim.sum()} bearish reclamations")
            
            return result
        
        except Exception as e:
            logger.error(f"Error detecting reclamations: {str(e)}")
            return pd.DataFrame()
    
    def _track_confirmation(self, data, result, ema, price_col):
        """
        Track confirmation of reclamations
        
        Parameters:
        -----------
        data : pandas.DataFrame
            Price data with OHLCV columns
        result : pandas.DataFrame
            DataFrame with reclamation signals
        ema : pandas.Series
            EMA values
        price_col : str
            Column name for price data
            
        Returns:
        --------
        pandas.DataFrame
            Updated result DataFrame with confirmation signals
        """
        # Initialize confirmation arrays
        bullish_confirmed = np.zeros(len(data), dtype=bool)
        bearish_confirmed = np.zeros(len(data), dtype=bool)
        
        # Track confirmation status for each reclamation
        for i in range(len(data)):
            # Check for invalid index
            if i >= len(result['BullishReclaim']) or i >= len(result['BearishReclaim']):
                continue
            
            # Handle bullish reclamations
            if result['BullishReclaim'].iloc[i]:
                # Check if price stays above EMA for the confirmation period
                if i + self.confirmation_bars < len(data):
                    confirmed = True
                    for j in range(1, self.confirmation_bars + 1):
                        # Skip if index is out of bounds
                        if i+j >= len(data) or i+j >= len(ema):
                            confirmed = False
                            break
                        
                        curr_price = data[price_col].iloc[i + j]
                        curr_ema = ema.iloc[i + j]
                        
                        # Convert to scalars if Series
                        if isinstance(curr_price, pd.Series):
                            curr_price = curr_price.iloc[0]
                        if isinstance(curr_ema, pd.Series):
                            curr_ema = curr_ema.iloc[0]
                        
                        # If price drops below EMA, confirmation fails
                        if curr_price < curr_ema:
                            confirmed = False
                            break
                    
                    # If confirmed, mark it
                    if confirmed:
                        bullish_confirmed[i] = True
                        
                        # Update the reclamation details
                        for details in self.reclamation_details['bullish']:
                            if details['index'] == i:
                                details['confirmed'] = True
                                details['confirmation_index'] = i + self.confirmation_bars
                                break
            
            # Handle bearish reclamations
            elif result['BearishReclaim'].iloc[i]:
                # Check if price stays below EMA for the confirmation period
                if i + self.confirmation_bars < len(data):
                    confirmed = True
                    for j in range(1, self.confirmation_bars + 1):
                        # Skip if index is out of bounds
                        if i+j >= len(data) or i+j >= len(ema):
                            confirmed = False
                            break
                        
                        curr_price = data[price_col].iloc[i + j]
                        curr_ema = ema.iloc[i + j]
                        
                        # Convert to scalars if Series
                        if isinstance(curr_price, pd.Series):
                            curr_price = curr_price.iloc[0]
                        if isinstance(curr_ema, pd.Series):
                            curr_ema = curr_ema.iloc[0]
                        
                        # If price rises above EMA, confirmation fails
                        if curr_price > curr_ema:
                            confirmed = False
                            break
                    
                    # If confirmed, mark it
                    if confirmed:
                        bearish_confirmed[i] = True
                        
                        # Update the reclamation details
                        for details in self.reclamation_details['bearish']:
                            if details['index'] == i:
                                details['confirmed'] = True
                                details['confirmation_index'] = i + self.confirmation_bars
                                break
        
        # Add confirmation signals to result
        result['BullishConfirmed'] = bullish_confirmed
        result['BearishConfirmed'] = bearish_confirmed
        
        return result
    
    def detect_pullbacks(self, data, reclamation_data=None, fib_tools=None):
        """
        Detect pullbacks after EMA reclamations
        
        Parameters:
        -----------
        data : pandas.DataFrame
            Price data with OHLCV columns
        reclamation_data : pandas.DataFrame, optional
            Pre-calculated reclamation data
        fib_tools : FibonacciTools, optional
            FibonacciTools instance for validating pullbacks
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with pullback signals
        """
        if reclamation_data is None:
            reclamation_data = self.detect_reclamation(data)
        
        if reclamation_data.empty:
            return pd.DataFrame()
        
        # Initialize result DataFrame
        result = pd.DataFrame(index=data.index)
        result['BullishPullback'] = False
        result['BearishPullback'] = False
        
        # Import FibonacciTools if needed
        if fib_tools is None:
            from mtfema_backtester.indicators.fibonacci import FibonacciTools
            fib_tools = FibonacciTools()
        
        # Process bullish reclamations
        for reclaim in self.reclamation_details['bullish']:
            if not reclaim['confirmed']:
                continue
            
            reclaim_idx = reclaim['index']
            confirm_idx = reclaim['confirmation_index']
            
            if confirm_idx is None or confirm_idx >= len(data) - 1:
                continue
            
            # Look for pullbacks after confirmation
            for i in range(confirm_idx + 1, len(data)):
                current_price = data['Close'].iloc[i]
                reclaim_price = reclaim['reclaim_price']
                reclaim_low = reclaim['reclaim_low']
                
                # Define swing points for Fibonacci calculation
                swing_low = reclaim_low
                swing_high = data['High'].iloc[i-1]  # Use recent high
                
                # Check if price has pulled back to Fibonacci zone
                if fib_tools.validate_pullback(
                    current_price, swing_high, swing_low, reclaim_price, is_long=True
                ):
                    result['BullishPullback'].iloc[i] = True
                    
                    # Update reclamation details
                    reclaim['pullback_detected'] = True
                    reclaim['pullback_price'] = current_price
                    reclaim['pullback_index'] = i
                    break
        
        # Process bearish reclamations
        for reclaim in self.reclamation_details['bearish']:
            if not reclaim['confirmed']:
                continue
            
            reclaim_idx = reclaim['index']
            confirm_idx = reclaim['confirmation_index']
            
            if confirm_idx is None or confirm_idx >= len(data) - 1:
                continue
            
            # Look for pullbacks after confirmation
            for i in range(confirm_idx + 1, len(data)):
                current_price = data['Close'].iloc[i]
                reclaim_price = reclaim['reclaim_price']
                reclaim_high = reclaim['reclaim_high']
                
                # Define swing points for Fibonacci calculation
                swing_high = reclaim_high
                swing_low = data['Low'].iloc[i-1]  # Use recent low
                
                # Check if price has pulled back to Fibonacci zone
                if fib_tools.validate_pullback(
                    current_price, swing_high, swing_low, reclaim_price, is_long=False
                ):
                    result['BearishPullback'].iloc[i] = True
                    
                    # Update reclamation details
                    reclaim['pullback_detected'] = True
                    reclaim['pullback_price'] = current_price
                    reclaim['pullback_index'] = i
                    break
        
        logger.info(f"Detected {result['BullishPullback'].sum()} bullish and "
                   f"{result['BearishPullback'].sum()} bearish pullbacks")
        
        return result
    
    def get_reclamation_details(self, direction='bullish', confirmed_only=True):
        """
        Get details of EMA reclamations
        
        Parameters:
        -----------
        direction : str
            'bullish', 'bearish', or 'both'
        confirmed_only : bool
            If True, return only confirmed reclamations
            
        Returns:
        --------
        list
            List of reclamation details dictionaries
        """
        result = []
        
        if direction.lower() in ['bullish', 'both']:
            for reclaim in self.reclamation_details['bullish']:
                if confirmed_only and not reclaim['confirmed']:
                    continue
                result.append(reclaim)
        
        if direction.lower() in ['bearish', 'both']:
            for reclaim in self.reclamation_details['bearish']:
                if confirmed_only and not reclaim['confirmed']:
                    continue
                result.append(reclaim)
        
        return result
    
    def get_pullback_details(self, direction='both'):
        """
        Get details of pullbacks after EMA reclamations
        
        Parameters:
        -----------
        direction : str
            'bullish', 'bearish', or 'both'
            
        Returns:
        --------
        list
            List of pullback details dictionaries
        """
        result = []
        
        if direction.lower() in ['bullish', 'both']:
            for reclaim in self.reclamation_details['bullish']:
                if reclaim['pullback_detected']:
                    result.append(reclaim)
        
        if direction.lower() in ['bearish', 'both']:
            for reclaim in self.reclamation_details['bearish']:
                if reclaim['pullback_detected']:
                    result.append(reclaim)
        
        return result
    
    def reset(self):
        """Clear all stored reclamation details"""
        self.reclamation_details = {
            'bullish': [],
            'bearish': []
        }
        logger.info("ReclamationDetector reset to initial state")
