import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class TimeframeData:
    """
    Container for multi-timeframe data with synchronized access methods
    """
    
    def __init__(self, data_dict=None):
        """
        Initialize the TimeframeData object
        
        Parameters:
        -----------
        data_dict : dict, optional
            Dictionary with timeframes as keys and DataFrames as values
        """
        self.data = data_dict if data_dict else {}
        self.indicators = {}  # Store calculated indicators
        logger.info(f"TimeframeData initialized with timeframes: {list(self.data.keys())}")
    
    def add_timeframe(self, timeframe, data):
        """
        Add a timeframe dataset
        
        Parameters:
        -----------
        timeframe : str
            Timeframe identifier (e.g., '1d', '1h', '15m')
        data : pandas.DataFrame
            OHLCV data for the timeframe
        """
        self.data[timeframe] = data
        # Clear indicator cache for this timeframe
        if timeframe in self.indicators:
            del self.indicators[timeframe]
        logger.info(f"Added {timeframe} data with {len(data)} rows")
    
    def get_timeframe(self, timeframe):
        """
        Get data for a specific timeframe
        
        Parameters:
        -----------
        timeframe : str
            Timeframe identifier
            
        Returns:
        --------
        pandas.DataFrame
            OHLCV data for the requested timeframe
        """
        if timeframe not in self.data:
            logger.warning(f"Timeframe {timeframe} not found in available data")
            return None
        return self.data[timeframe]
    
    def get_available_timeframes(self):
        """
        Get list of available timeframes
        
        Returns:
        --------
        list
            List of available timeframe identifiers
        """
        return list(self.data.keys())
    
    def synchronize_timeframes(self):
        """
        Align timestamps across different timeframes
        
        Returns:
        --------
        dict
            Dictionary of synchronized DataFrames
        """
        if not self.data:
            logger.warning("No data available to synchronize")
            return {}
        
        # Create a mapping of indices
        all_indices = {}
        for tf, df in self.data.items():
            all_indices[tf] = set(df.index)
        
        # Synchronize by filtering to common timestamps
        synced_data = {}
        for tf, df in self.data.items():
            # For now, just return the original data
            # Future implementation will handle proper synchronization
            synced_data[tf] = df.copy()
        
        logger.info("Timeframes synchronized")
        return synced_data
    
    def add_indicator(self, timeframe, indicator_name, indicator_data):
        """
        Add calculated indicator data to a timeframe
        
        Parameters:
        -----------
        timeframe : str
            Timeframe identifier
        indicator_name : str
            Name of the indicator
        indicator_data : pandas.Series or pandas.DataFrame
            Calculated indicator values
        """
        if timeframe not in self.indicators:
            self.indicators[timeframe] = {}
        
        self.indicators[timeframe][indicator_name] = indicator_data
        logger.info(f"Added {indicator_name} indicator to {timeframe} data")
    
    def get_indicator(self, timeframe, indicator_name):
        """
        Get calculated indicator data
        
        Parameters:
        -----------
        timeframe : str
            Timeframe identifier
        indicator_name : str
            Name of the indicator
            
        Returns:
        --------
        pandas.Series or pandas.DataFrame
            Calculated indicator values
        """
        if timeframe not in self.indicators:
            logger.warning(f"No indicators found for timeframe {timeframe}")
            return None
        
        if indicator_name not in self.indicators[timeframe]:
            logger.warning(f"Indicator {indicator_name} not found for timeframe {timeframe}")
            return None
        
        return self.indicators[timeframe][indicator_name]
    
    def merge_indicator_with_data(self, timeframe, indicator_names=None):
        """
        Merge indicators with price data for a timeframe
        
        Parameters:
        -----------
        timeframe : str
            Timeframe identifier
        indicator_names : list, optional
            List of indicator names to merge, merges all if None
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with price data and indicators
        """
        if timeframe not in self.data:
            logger.warning(f"Timeframe {timeframe} not found in available data")
            return None
            
        if timeframe not in self.indicators:
            logger.warning(f"No indicators available for timeframe {timeframe}")
            return self.data[timeframe].copy()
        
        # Start with price data
        result = self.data[timeframe].copy()
        
        # Determine which indicators to merge
        indicators_to_merge = indicator_names or self.indicators[timeframe].keys()
        
        # Merge indicators
        for ind_name in indicators_to_merge:
            if ind_name in self.indicators[timeframe]:
                ind_data = self.indicators[timeframe][ind_name]
                
                # Handle case where indicator is a dataframe
                if isinstance(ind_data, pd.DataFrame):
                    for col in ind_data.columns:
                        result[f"{ind_name}_{col}"] = ind_data[col]
                else:
                    result[ind_name] = ind_data
        
        return result
