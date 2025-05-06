"""
Logging utilities for the Multi-Timeframe 9 EMA Extension Strategy backtester.

This module provides a consistent logging setup for the project.
"""

import os
import logging
import datetime
from logging.handlers import RotatingFileHandler

def setup_logger(log_dir, name=None, level=logging.INFO):
    """
    Set up and configure logger
    
    Parameters:
    -----------
    log_dir : str
        Directory to store log files
    name : str, optional
        Logger name (default: root logger)
    level : int, optional
        Logging level (default: INFO)
        
    Returns:
    --------
    logging.Logger
        Configured logger
    """
    # Create log directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)
    
    # Get logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatters
    simple_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    
    # Create file handler with timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = os.path.join(log_dir, f'backtester_{timestamp}.log')
    
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(detailed_formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    logger.info(f"Logger initialized. Log file: {log_file}")
    return logger
