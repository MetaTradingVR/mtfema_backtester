"""
Data loader utility for the Multi-Timeframe 9 EMA Extension Strategy.

This module handles loading price data from various sources.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import yfinance as yf

logger = logging.getLogger(__name__)

class DataLoader:
    """
    Load and cache financial data from various sources
    """
    
    def __init__(self, cache_dir='./data/cache', cache_expiry_days=1):
        """
        Initialize the DataLoader
        
        Parameters:
        -----------
        cache_dir : str
            Directory to store cached data
        cache_expiry_days : int
            Number of days before cache expires
        """
        self.cache_dir = cache_dir
        self.cache_expiry_days = cache_expiry_days
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        logger.info(f"DataLoader initialized with cache directory: {cache_dir}")
    
    def get_data(self, symbol, timeframe, start_date, end_date=None, source='yahoo', use_cache=True):
        """
        Get financial data for a symbol
        
        Parameters:
        -----------
        symbol : str
            Symbol to get data for
        timeframe : str
            Timeframe for data ('1d', '1h', '15m', etc.)
        start_date : str
            Start date in format 'YYYY-MM-DD'
        end_date : str
            End date in format 'YYYY-MM-DD'
        source : str
            Data source ('yahoo', 'csv', etc.)
        use_cache : bool
            Whether to use cached data if available
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with OHLCV data
        """
        # Set end date to today if not provided
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
            
        # Check if we have cached data
        if use_cache:
            cache_file = self._get_cache_path(symbol, timeframe, start_date, end_date)
            
            if os.path.exists(cache_file):
                if not self._is_cache_expired(cache_file):
                    logger.info(f"Loading cached data for {symbol} ({timeframe}) from {cache_file}")
                    df = self._load_from_cache(cache_file)
                    
                    # Verify that we have data
                    if df is not None and not df.empty:
                        return df
                    else:
                        logger.warning(f"Cached data for {symbol} ({timeframe}) is empty, redownloading")
                else:
                    logger.info(f"Cached data for {symbol} ({timeframe}) is expired, redownloading")
            else:
                logger.info(f"No cached data for {symbol} ({timeframe})")
        
        # Download fresh data
        if source.lower() == 'yahoo':
            logger.info(f"Downloading {symbol} data with {timeframe} timeframe from {start_date} to {end_date}")
            df = self._download_yahoo_data(symbol, timeframe, start_date, end_date)
        elif source.lower() == 'csv':
            logger.error(f"CSV source not implemented yet")
            return None
        else:
            logger.error(f"Unknown data source: {source}")
            return None
        
        # Cache the data
        if df is not None and not df.empty and use_cache:
            cache_file = self._get_cache_path(symbol, timeframe, start_date, end_date)
            logger.info(f"Cached {symbol} ({timeframe}) data to {cache_file}")
            self._save_to_cache(df, cache_file)
        
        return df
    
    def _get_cache_path(self, symbol, timeframe, start_date, end_date):
        """Get the path to the cache file"""
        filename = f"{symbol}_{timeframe}_{start_date}_{end_date}.csv"
        return os.path.join(self.cache_dir, filename)
    
    def _is_cache_expired(self, cache_file):
        """Check if the cached data is expired"""
        file_modified_time = os.path.getmtime(cache_file)
        file_modified_date = datetime.fromtimestamp(file_modified_time)
        expiry_date = datetime.now() - timedelta(days=self.cache_expiry_days)
        
        return file_modified_date < expiry_date
    
    def _save_to_cache(self, df, cache_file):
        """Save data to cache file"""
        try:
            df.to_csv(cache_file)
            return True
        except Exception as e:
            logger.error(f"Error saving to cache: {str(e)}")
            return False
    
    def _load_from_cache(self, cache_file):
        """Load data from cache file"""
        try:
            # Read CSV with explicit numeric columns
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            
            # Ensure all price and volume columns are numeric
            numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in df.columns:
                # Handle both regular column names and MultiIndex columns
                col_name = col[0] if isinstance(col, tuple) else col
                if col_name in numeric_cols:
                    if isinstance(col, tuple):
                        df[(col_name, col[1])] = pd.to_numeric(df[(col_name, col[1])], errors='coerce')
                    else:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
        except Exception as e:
            logger.error(f"Error loading from cache: {str(e)}")
            return None
    
    def _download_yahoo_data(self, symbol, timeframe, start_date, end_date):
        """Download data from Yahoo Finance"""
        try:
            # Convert timeframe to yfinance interval
            interval = self._convert_timeframe_to_yf_interval(timeframe)
            
            # Download data
            df = yf.download(
                tickers=symbol,
                start=start_date,
                end=end_date,
                interval=interval,
                progress=False
            )
            
            # Make sure the index is a DatetimeIndex
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            
            # Ensure all columns are numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Create MultiIndex columns to match the format in TimeframeData
            # Only if we don't already have a MultiIndex
            if not isinstance(df.columns, pd.MultiIndex):
                df.columns = pd.MultiIndex.from_product([df.columns, [symbol]])
            
            return df
        
        except Exception as e:
            logger.error(f"Error downloading data from Yahoo Finance: {str(e)}")
            return None
    
    def _convert_timeframe_to_yf_interval(self, timeframe):
        """Convert timeframe string to yfinance interval"""
        # Common timeframes
        timeframe_map = {
            '1m': '1m',
            '5m': '5m',
            '10m': '15m',  # Yahoo doesn't have 10m
            '15m': '15m',
            '30m': '30m',
            '1h': '1h',
            '2h': '2h',
            '4h': '4h',
            '1d': '1d',
            '1w': '1wk',
            '1M': '1mo'
        }
        
        if timeframe in timeframe_map:
            return timeframe_map[timeframe]
        else:
            logger.warning(f"Unknown timeframe: {timeframe}, using 1d")
            return '1d'
    
    def get_multi_timeframe_data(self, symbol, timeframes, start_date, end_date=None, use_cache=True):
        """
        Get data for multiple timeframes for a symbol
        
        Parameters:
        -----------
        symbol : str
            Trading symbol (e.g., 'AAPL')
        timeframes : list
            List of timeframes (e.g., ['1d', '1h', '15m'])
        start_date : str
            Start date in format 'YYYY-MM-DD'
        end_date : str, optional
            End date in format 'YYYY-MM-DD', defaults to today
        use_cache : bool
            Whether to use cached data if available
            
        Returns:
        --------
        dict
            Dictionary with timeframes as keys and DataFrames as values
        """
        result = {}
        
        for tf in timeframes:
            data = self.get_data(symbol, tf, start_date, end_date, use_cache=use_cache)
            if data is not None and not data.empty:
                result[tf] = data
        
        return result
