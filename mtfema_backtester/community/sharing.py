"""
Community features for the MT 9 EMA Backtester

This module handles sharing strategy results, setups, and signals with the
MT 9 EMA strategy community.
"""

import json
import requests
import pandas as pd
import os
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
import base64
import hashlib

logger = logging.getLogger(__name__)

class CommunityConnect:
    """Community connection and sharing functionality."""
    
    def __init__(self, api_url: str = "https://mt9ema-community.com/api", api_key: Optional[str] = None):
        """
        Initialize connection to the MT 9 EMA community platform.
        
        Args:
            api_url: API endpoint for the community platform
            api_key: API key for authenticating with the community platform
        """
        self.api_url = api_url
        self.api_key = api_key
        self.user_id = None
        self.username = None
        self.is_connected = False
    
    def connect(self, username: str, password: str) -> bool:
        """
        Connect to the community platform.
        
        Args:
            username: Username for authentication
            password: Password for authentication
            
        Returns:
            True if connected successfully, False otherwise
        """
        try:
            # In a real implementation, this would make an actual API call
            # For now, just simulate a successful connection
            auth_data = {
                "username": username,
                "password": password
            }
            
            # Simulate API response
            # In a real implementation, this would come from the API
            response = {
                "success": True,
                "user_id": str(uuid.uuid4()),
                "username": username,
                "api_key": f"key_{username}_{str(uuid.uuid4())[:8]}"
            }
            
            if response.get("success", False):
                self.user_id = response["user_id"]
                self.username = response["username"]
                self.api_key = response["api_key"]
                self.is_connected = True
                
                logger.info(f"Connected to MT 9 EMA community as {username}")
                return True
            else:
                logger.error(f"Failed to connect to community: {response.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to community: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from the community platform.
        
        Returns:
            True if disconnected successfully
        """
        self.user_id = None
        self.username = None
        self.is_connected = False
        
        logger.info("Disconnected from MT 9 EMA community")
        return True
    
    def share_backtest_results(self, backtest_result: Any, description: str = "") -> Dict[str, Any]:
        """
        Share backtest results with the community.
        
        Args:
            backtest_result: Backtest result object
            description: Description of the backtest
            
        Returns:
            Response from the community API
        """
        if not self.is_connected:
            logger.error("Not connected to community platform")
            return {"success": False, "error": "Not connected"}
        
        try:
            # Extract key metrics from backtest
            metrics = backtest_result.metrics
            
            # Prepare data for sharing
            share_data = {
                "user_id": self.user_id,
                "username": self.username,
                "timestamp": datetime.now().isoformat(),
                "strategy_name": backtest_result.strategy_name,
                "symbols": backtest_result.symbols,
                "timeframes": backtest_result.timeframes,
                "description": description,
                "metrics": {
                    "total_trades": metrics.get("total_trades", 0),
                    "win_rate": metrics.get("win_rate", 0),
                    "profit_factor": metrics.get("profit_factor", 0),
                    "total_return": metrics.get("total_return", 0),
                    "max_drawdown": metrics.get("max_drawdown_pct", 0),
                    "sharpe_ratio": metrics.get("sharpe_ratio", 0)
                },
                "total_trades": len(backtest_result.trades),
                "initial_capital": backtest_result.initial_capital,
                "final_equity": metrics.get("final_equity", backtest_result.initial_capital)
            }
            
            # In a real implementation, this would make an API call
            # Simulate API response
            response = {
                "success": True,
                "share_id": str(uuid.uuid4()),
                "url": f"https://mt9ema-community.com/backtests/{str(uuid.uuid4())}"
            }
            
            logger.info(f"Shared backtest results: {response.get('url')}")
            return response
            
        except Exception as e:
            logger.error(f"Error sharing backtest results: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def share_trading_setup(self, setup: Dict[str, Any]) -> Dict[str, Any]:
        """
        Share a trading setup with the community.
        
        Args:
            setup: Trading setup details
            
        Returns:
            Response from the community API
        """
        if not self.is_connected:
            logger.error("Not connected to community platform")
            return {"success": False, "error": "Not connected"}
        
        try:
            # Prepare setup data
            setup_data = {
                "user_id": self.user_id,
                "username": self.username,
                "timestamp": datetime.now().isoformat(),
                "symbol": setup.get("symbol"),
                "timeframe": setup.get("timeframe"),
                "setup_type": setup.get("setup_type", "MT9EMA"),
                "direction": setup.get("direction"),
                "entry_price": setup.get("entry_price"),
                "stop_loss": setup.get("stop_loss"),
                "take_profit": setup.get("take_profit"),
                "risk_reward": setup.get("risk_reward"),
                "description": setup.get("description", ""),
                "screenshot": setup.get("screenshot")  # Base64 encoded image
            }
            
            # In a real implementation, this would make an API call
            # Simulate API response
            response = {
                "success": True,
                "setup_id": str(uuid.uuid4()),
                "url": f"https://mt9ema-community.com/setups/{str(uuid.uuid4())}"
            }
            
            logger.info(f"Shared trading setup: {response.get('url')}")
            return response
            
        except Exception as e:
            logger.error(f"Error sharing trading setup: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_community_setups(self, 
                           symbol: Optional[str] = None, 
                           timeframe: Optional[str] = None,
                           setup_type: Optional[str] = None,
                           limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get setups shared by the community.
        
        Args:
            symbol: Filter by symbol
            timeframe: Filter by timeframe
            setup_type: Filter by setup type
            limit: Maximum number of setups to retrieve
            
        Returns:
            List of setup dictionaries
        """
        if not self.is_connected:
            logger.error("Not connected to community platform")
            return []
        
        try:
            # Prepare query parameters
            params = {
                "limit": limit
            }
            
            if symbol:
                params["symbol"] = symbol
            
            if timeframe:
                params["timeframe"] = timeframe
            
            if setup_type:
                params["setup_type"] = setup_type
            
            # In a real implementation, this would make an API call
            # Simulate API response with sample data
            setups = []
            
            # Generate some sample setups
            sample_symbols = ["ES", "NQ", "CL", "GC", "EURUSD", "AAPL", "MSFT"]
            sample_timeframes = ["5m", "15m", "1h", "4h", "1d"]
            sample_directions = ["buy", "sell"]
            
            for i in range(limit):
                sample_symbol = sample_symbols[i % len(sample_symbols)]
                
                # Skip if we're filtering by symbol and it doesn't match
                if symbol and symbol != sample_symbol:
                    continue
                
                sample_tf = sample_timeframes[i % len(sample_timeframes)]
                
                # Skip if we're filtering by timeframe and it doesn't match
                if timeframe and timeframe != sample_tf:
                    continue
                
                sample_direction = sample_directions[i % len(sample_directions)]
                sample_price = 100 + (i * 5)
                
                setup = {
                    "setup_id": f"setup_{i}_{str(uuid.uuid4())[:8]}",
                    "user_id": f"user_{i % 10}",
                    "username": f"trader{i % 10}",
                    "timestamp": (datetime.now().replace(hour=i%24, minute=i%60)).isoformat(),
                    "symbol": sample_symbol,
                    "timeframe": sample_tf,
                    "setup_type": "MT9EMA",
                    "direction": sample_direction,
                    "entry_price": sample_price,
                    "stop_loss": sample_price * (0.95 if sample_direction == "buy" else 1.05),
                    "take_profit": sample_price * (1.15 if sample_direction == "buy" else 0.85),
                    "risk_reward": 3.0,
                    "description": f"MT 9 EMA extension setup on {sample_symbol} {sample_tf}",
                    "likes": i % 50,
                    "comments": i % 10,
                    "url": f"https://mt9ema-community.com/setups/sample{i}"
                }
                
                setups.append(setup)
            
            logger.info(f"Retrieved {len(setups)} community setups")
            return setups
            
        except Exception as e:
            logger.error(f"Error getting community setups: {str(e)}")
            return []
    
    def get_community_performance(self, timeframe: str = "all") -> Dict[str, Any]:
        """
        Get community performance statistics.
        
        Args:
            timeframe: Time period for stats ("day", "week", "month", "year", "all")
            
        Returns:
            Dictionary with community performance statistics
        """
        if not self.is_connected:
            logger.error("Not connected to community platform")
            return {}
        
        try:
            # In a real implementation, this would make an API call
            # Simulate API response with sample data
            
            # Performance metrics vary based on timeframe
            multiplier = 1
            if timeframe == "week":
                multiplier = 0.8
            elif timeframe == "month":
                multiplier = 0.7
            elif timeframe == "year":
                multiplier = 0.6
            elif timeframe == "all":
                multiplier = 0.5
            
            performance = {
                "timeframe": timeframe,
                "total_users": 1250,
                "active_users": 850,
                "total_setups_shared": 12500,
                "total_backtests_shared": 3200,
                "avg_win_rate": 62.5 * multiplier,
                "avg_profit_factor": 1.8 * multiplier,
                "avg_sharpe_ratio": 1.2 * multiplier,
                "top_symbols": [
                    {"symbol": "ES", "count": 2500},
                    {"symbol": "NQ", "count": 1800},
                    {"symbol": "EURUSD", "count": 1500},
                    {"symbol": "AAPL", "count": 1200},
                    {"symbol": "TSLA", "count": 900}
                ],
                "top_timeframes": [
                    {"timeframe": "1h", "count": 3500},
                    {"timeframe": "4h", "count": 2800},
                    {"timeframe": "1d", "count": 2200},
                    {"timeframe": "15m", "count": 1800},
                    {"timeframe": "5m", "count": 1200}
                ]
            }
            
            logger.info(f"Retrieved community performance for timeframe: {timeframe}")
            return performance
            
        except Exception as e:
            logger.error(f"Error getting community performance: {str(e)}")
            return {}
    
    def like_setup(self, setup_id: str) -> bool:
        """
        Like a community setup.
        
        Args:
            setup_id: ID of the setup to like
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_connected:
            logger.error("Not connected to community platform")
            return False
        
        try:
            # In a real implementation, this would make an API call
            # Simulate API response
            response = {
                "success": True,
                "setup_id": setup_id,
                "likes": 42  # New like count
            }
            
            logger.info(f"Liked setup {setup_id}")
            return response.get("success", False)
            
        except Exception as e:
            logger.error(f"Error liking setup: {str(e)}")
            return False
    
    def comment_on_setup(self, setup_id: str, comment: str) -> Dict[str, Any]:
        """
        Add a comment to a community setup.
        
        Args:
            setup_id: ID of the setup to comment on
            comment: Comment text
            
        Returns:
            Response from the community API
        """
        if not self.is_connected:
            logger.error("Not connected to community platform")
            return {"success": False, "error": "Not connected"}
        
        try:
            # Prepare comment data
            comment_data = {
                "user_id": self.user_id,
                "username": self.username,
                "setup_id": setup_id,
                "comment": comment,
                "timestamp": datetime.now().isoformat()
            }
            
            # In a real implementation, this would make an API call
            # Simulate API response
            response = {
                "success": True,
                "comment_id": str(uuid.uuid4()),
                "setup_id": setup_id,
                "comments": 15  # New comment count
            }
            
            logger.info(f"Added comment to setup {setup_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error commenting on setup: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def upload_screenshot(self, image_path: str) -> str:
        """
        Upload a screenshot to the community platform.
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string or URL
        """
        try:
            # Read image file and encode as base64
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            
            # In a real implementation, this might upload the image to a server
            # and return a URL instead of the base64 string
            
            logger.info(f"Uploaded screenshot: {image_path}")
            return encoded_string
            
        except Exception as e:
            logger.error(f"Error uploading screenshot: {str(e)}")
            return ""
    
    def get_leaderboard(self, timeframe: str = "month", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the community leaderboard.
        
        Args:
            timeframe: Time period for leaderboard ("day", "week", "month", "year", "all")
            limit: Maximum number of users to retrieve
            
        Returns:
            List of user dictionaries with performance metrics
        """
        if not self.is_connected:
            logger.error("Not connected to community platform")
            return []
        
        try:
            # In a real implementation, this would make an API call
            # Simulate API response with sample data
            users = []
            
            for i in range(limit):
                win_rate = 75 - (i * 2)  # Decreasing win rates from top to bottom
                profit_factor = 2.5 - (i * 0.15)
                
                user = {
                    "rank": i + 1,
                    "user_id": f"user_{i}",
                    "username": f"trader{i}",
                    "win_rate": win_rate,
                    "profit_factor": profit_factor,
                    "total_return": (50 - i * 3),
                    "total_trades": 100 + (i * 20),
                    "sharpe_ratio": 1.8 - (i * 0.1),
                    "max_drawdown": 10 + (i * 0.8)
                }
                
                users.append(user)
            
            logger.info(f"Retrieved leaderboard for timeframe: {timeframe}")
            return users
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {str(e)}")
            return []
