#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data fetcher for the MTFEMA Backtester web interface

This module provides functions to fetch price data from various sources
and convert it to TimeframeData objects for use in the backtester.

Timestamp: 2025-05-06 PST
"""

import os
import logging
import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf

from mtfema_backtester.data.timeframe_data import TimeframeData

logger = logging.getLogger(__name__)

def fetch_yahoo_finance_data(symbol, start_date, end_date, timeframes=None):
    """
    Fetch price data from Yahoo Finance
    
    Parameters:
    -----------
    symbol : str
        The symbol to fetch data for
    start_date : datetime.date
        Start date for data
    end_date : datetime.date
        End date for data
    timeframes : list, optional
        List of timeframes to fetch, defaults to ['1d']
        Available: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        
    Returns:
    --------
    TimeframeData
        TimeframeData object with the requested timeframes
    """
    if timeframes is None:
        timeframes = ['1d']
    
    # Map our timeframe format to Yahoo's
    timeframe_map = {
        '1m': '1m',
        '5m': '5m',
        '15m': '15m',
        '30m': '30m',
        '1h': '60m',
        '4h': '4h',  # Not directly supported, will need to resample
        '1d': '1d',
        '1w': '1wk'
    }
    
    # Create a TimeframeData object
    tf_data = TimeframeData()
    
    # Add buffer days for resampling higher timeframes
    buffer_days = 10
    buffered_start = start_date - timedelta(days=buffer_days)
    
    try:
        for tf in timeframes:
            # Check if timeframe is supported
            if tf not in timeframe_map:
                logger.warning(f"Timeframe {tf} not supported, skipping")
                continue
            
            yahoo_tf = timeframe_map[tf]
            
            # Special handling for 4h which needs resampling
            if tf == '4h':
                # Fetch 1h data and resample
                logger.info(f"Fetching 1h data for {symbol} to resample to 4h")
                data_1h = yf.download(
                    symbol,
                    start=buffered_start,
                    end=end_date,
                    interval='60m',
                    progress=False
                )
                
                if data_1h.empty:
                    logger.warning(f"No 1h data found for {symbol}, skipping 4h timeframe")
                    continue
                
                # Resample to 4h
                data = data_1h.resample('4H').agg({
                    'Open': 'first',
                    'High': 'max',
                    'Low': 'min',
                    'Close': 'last',
                    'Volume': 'sum'
                })
                
                # Filter to requested date range
                data = data.loc[start_date:end_date]
            else:
                # For all other timeframes, fetch directly
                logger.info(f"Fetching {yahoo_tf} data for {symbol}")
                data = yf.download(
                    symbol,
                    start=start_date if tf in ['1d', '1w'] else buffered_start,
                    end=end_date,
                    interval=yahoo_tf,
                    progress=False
                )
            
            if data.empty:
                logger.warning(f"No data found for {symbol} with timeframe {tf}")
                continue
            
            # Add the data to our TimeframeData object
            tf_data.add_timeframe(tf, data)
            logger.info(f"Added {len(data)} rows of {tf} data for {symbol}")
        
        return tf_data
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return None

def calculate_indicators(timeframe_data, ema_period=9):
    """
    Calculate indicators for the data
    
    Parameters:
    -----------
    timeframe_data : TimeframeData
        TimeframeData object with price data
    ema_period : int, optional
        Period for EMA calculation, defaults to 9
        
    Returns:
    --------
    TimeframeData
        TimeframeData object with indicators added
    """
    try:
        # Get available timeframes
        timeframes = timeframe_data.get_available_timeframes()
        
        for tf in timeframes:
            # Get the data for this timeframe
            data = timeframe_data.get_timeframe(tf)
            
            if data is None or data.empty:
                logger.warning(f"No data for timeframe {tf}, skipping indicator calculation")
                continue
            
            # Calculate EMA
            ema_col = f"EMA_{ema_period}"
            data[ema_col] = data['Close'].ewm(span=ema_period, adjust=False).mean()
            
            # Calculate extension percentage
            data['Extension'] = 100 * (data['Close'] - data[ema_col]) / data[ema_col]
            
            # Calculate Bollinger Bands
            sma_20 = data['Close'].rolling(window=20).mean()
            std_20 = data['Close'].rolling(window=20).std()
            
            data['BB_Upper'] = sma_20 + (std_20 * 2)
            data['BB_Middle'] = sma_20
            data['BB_Lower'] = sma_20 - (std_20 * 2)
            
            # Calculate ATR for risk management
            high_low = data['High'] - data['Low']
            high_close = (data['High'] - data['Close'].shift()).abs()
            low_close = (data['Low'] - data['Close'].shift()).abs()
            
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            data['ATR_14'] = tr.rolling(window=14).mean()
            
            # Add the calculated indicators back to the TimeframeData object
            timeframe_data.add_timeframe(tf, data)
            
            # Add any composite indicators that need multiple timeframes
            # (This would be done after processing all individual timeframes)
        
        return timeframe_data
        
    except Exception as e:
        logger.error(f"Error calculating indicators: {str(e)}")
        return timeframe_data

def generate_sample_data(timeframes=None, periods=100):
    """
    Generate sample price data for testing
    
    Parameters:
    -----------
    timeframes : list, optional
        List of timeframes to generate, defaults to ['1d']
    periods : int, optional
        Number of periods to generate, defaults to 100
        
    Returns:
    --------
    TimeframeData
        TimeframeData object with sample data
    """
    if timeframes is None:
        timeframes = ['1d']
    
    # Create a TimeframeData object
    tf_data = TimeframeData()
    
    # Base timestamp for generation
    base_time = datetime.now() - timedelta(days=periods)
    
    for tf in timeframes:
        # Determine interval in minutes
        if tf.endswith('m'):
            minutes = int(tf[:-1])
        elif tf == '1h':
            minutes = 60
        elif tf == '4h':
            minutes = 240
        elif tf == '1d':
            minutes = 60 * 24
        elif tf == '1w':
            minutes = 60 * 24 * 7
        else:
            logger.warning(f"Unknown timeframe format: {tf}")
            continue
        
        # Generate timestamps
        timestamps = [base_time + timedelta(minutes=i * minutes) for i in range(periods)]
        
        # Generate price data with trending behavior
        close_price = 100.0
        data = []
        
        for i in range(periods):
            # Generate random price movement
            price_change = close_price * 0.01 * (0.5 - pd.np.random.random())
            close_price += price_change
            
            # Generate OHLC data
            open_price = close_price - (close_price * 0.005 * (0.5 - pd.np.random.random()))
            high_price = max(open_price, close_price) * (1 + 0.003 * pd.np.random.random())
            low_price = min(open_price, close_price) * (1 - 0.003 * pd.np.random.random())
            
            # Add some volume
            volume = pd.np.random.randint(1000, 10000)
            
            data.append({
                'Timestamp': timestamps[i],
                'Open': open_price,
                'High': high_price,
                'Low': low_price,
                'Close': close_price,
                'Volume': volume
            })
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df.set_index('Timestamp', inplace=True)
        
        # Add to TimeframeData
        tf_data.add_timeframe(tf, df)
    
    # Calculate indicators
    tf_data = calculate_indicators(tf_data)
    
    return tf_data 