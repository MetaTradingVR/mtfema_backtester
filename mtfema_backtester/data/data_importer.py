"""
Data import utilities for the MT 9 EMA Extension Strategy Backtester.

This module provides flexible data import from various sources including CSV files.
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
import os
import json

logger = logging.getLogger(__name__)

class DataImporter:
    """
    Flexible data importer for market data from various sources.
    """
    
    def __init__(self, data_dir="./data/external", config_dir="./data/configs"):
        """
        Initialize the data importer.
        
        Args:
            data_dir: Directory for storing imported data
            config_dir: Directory for storing import configurations
        """
        self.data_dir = Path(data_dir)
        self.config_dir = Path(config_dir)
        
        # Create directories if they don't exist
        self.data_dir.mkdir(exist_ok=True, parents=True)
        self.config_dir.mkdir(exist_ok=True, parents=True)
        
        # Load saved import configurations
        self.import_configs = self._load_import_configs()
        
    def _load_import_configs(self):
        """Load saved import configurations from disk."""
        configs = {}
        config_file = self.config_dir / "import_configs.json"
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    configs = json.load(f)
                logger.info(f"Loaded {len(configs)} import configurations")
            except Exception as e:
                logger.error(f"Error loading import configurations: {str(e)}")
                
        return configs
    
    def save_import_config(self, name, config):
        """Save an import configuration for future use."""
        self.import_configs[name] = config
        
        try:
            config_file = self.config_dir / "import_configs.json"
            with open(config_file, 'w') as f:
                json.dump(self.import_configs, f, indent=4)
            logger.info(f"Saved import configuration: {name}")
            return True
        except Exception as e:
            logger.error(f"Error saving import configuration: {str(e)}")
            return False
    
    def import_csv(self, file_path, config_name=None, format_config=None):
        """
        Import data from CSV file with configurable format.
        
        Args:
            file_path: Path to CSV file
            config_name: Name of saved configuration to use
            format_config: Custom format configuration
            
        Returns:
            DataFrame with standardized format or None if error
        """
        try:
            # Use saved config if specified
            if config_name and config_name in self.import_configs:
                format_config = self.import_configs[config_name]
            
            # Default format expects OHLCV + datetime
            if not format_config:
                format_config = {
                    'datetime_col': 'datetime',
                    'datetime_format': '%Y-%m-%d %H:%M:%S',
                    'ohlc_cols': {
                        'open': 'open',
                        'high': 'high', 
                        'low': 'low',
                        'close': 'close'
                    },
                    'volume_col': 'volume',
                    'timeframe': '1d',  # Default timeframe if not specified
                    'symbol': None,     # Symbol if not specified in data
                }
                
            # Read CSV
            df = pd.read_csv(file_path)
            logger.info(f"Loaded CSV with {len(df)} rows from {file_path}")
            
            # Map column names if needed
            remap_needed = False
            col_mapping = {}
            
            for target, source in format_config['ohlc_cols'].items():
                if source in df.columns and source != target:
                    col_mapping[source] = target
                    remap_needed = True
                    
            # Handle volume column
            if format_config['volume_col'] in df.columns and format_config['volume_col'] != 'volume':
                col_mapping[format_config['volume_col']] = 'volume'
                remap_needed = True
                    
            if remap_needed:
                df = df.rename(columns=col_mapping)
            
            # Process datetime
            datetime_col = format_config['datetime_col']
            if datetime_col in df.columns and datetime_col != 'datetime':
                if format_config.get('datetime_format'):
                    df['datetime'] = pd.to_datetime(df[datetime_col], 
                                               format=format_config['datetime_format'])
                else:
                    df['datetime'] = pd.to_datetime(df[datetime_col])
                    
                # Drop original datetime column if it's different
                if datetime_col != 'datetime':
                    df = df.drop(columns=[datetime_col])
            
            # Add timeframe column if not present
            if 'timeframe' not in df.columns and format_config.get('timeframe'):
                df['timeframe'] = format_config['timeframe']
                
            # Add symbol column if not present
            if 'symbol' not in df.columns and format_config.get('symbol'):
                df['symbol'] = format_config['symbol']
            
            # Ensure datetime is the index
            df = df.set_index('datetime', drop=False)
            
            return df
            
        except Exception as e:
            logger.error(f"Error importing CSV: {str(e)}")
            return None
            
    def save_imported_data(self, df, symbol, timeframe):
        """
        Save imported data to the data directory.
        
        Args:
            df: DataFrame with imported data
            symbol: Symbol name
            timeframe: Timeframe string
        
        Returns:
            Path to saved file
        """
        if df is None or df.empty:
            logger.error("Cannot save empty dataframe")
            return None
            
        file_name = f"{symbol.lower()}_{timeframe}_imported.csv"
        file_path = self.data_dir / file_name
        
        try:
            df.to_csv(file_path)
            logger.info(f"Saved imported data to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving imported data: {str(e)}")
            return None
