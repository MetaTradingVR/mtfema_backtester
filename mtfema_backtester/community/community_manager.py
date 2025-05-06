"""
Central community manager for the MT 9 EMA Backtester.

This module provides a single interface for all community features
including sharing, signals, and forums.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from .sharing import CommunityConnect
from .signals import SignalManager, TradingSignal
from .forums import ForumManager, ForumPost

logger = logging.getLogger(__name__)

class CommunityManager:
    """Central manager for all community features."""
    
    def __init__(self, api_url: str = "https://mt9ema-community.com/api", 
                storage_path: str = "./data/community"):
        """
        Initialize community manager.
        
        Args:
            api_url: API endpoint for the community platform
            storage_path: Path to store community data locally
        """
        self.api_url = api_url
        self.storage_path = storage_path
        
        # Create storage directory if it doesn't exist
        os.makedirs(storage_path, exist_ok=True)
        
        # Initialize components
        self.connect = CommunityConnect(api_url=api_url)
        self.signals = SignalManager(
            community_api_url=api_url,
            local_storage_path=os.path.join(storage_path, "signals")
        )
        self.forums = ForumManager(
            api_url=f"{api_url}/forums",
            local_storage_path=os.path.join(storage_path, "forums")
        )
        
        # Authentication state
        self.is_authenticated = False
        self.user_id = None
        self.username = None
        
        logger.info("Community manager initialized")
    
    def login(self, username: str, password: str) -> bool:
        """
        Login to the community platform.
        
        Args:
            username: Username for authentication
            password: Password for authentication
            
        Returns:
            True if login successful, False otherwise
        """
        # Login using the community connect component
        success = self.connect.connect(username, password)
        
        if success:
            self.is_authenticated = True
            self.user_id = self.connect.user_id
            self.username = self.connect.username
            
            logger.info(f"Logged in as {username}")
        else:
            logger.error(f"Login failed for {username}")
        
        return success
    
    def logout(self) -> bool:
        """
        Logout from the community platform.
        
        Returns:
            True if successful
        """
        # Disconnect from the community platform
        self.connect.disconnect()
        
        # Reset authentication state
        self.is_authenticated = False
        self.user_id = None
        self.username = None
        
        logger.info("Logged out of community platform")
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
        self._check_authentication()
        return self.connect.share_backtest_results(backtest_result, description)
    
    def share_trading_setup(self, setup: Dict[str, Any]) -> Dict[str, Any]:
        """
        Share a trading setup with the community.
        
        Args:
            setup: Trading setup details
            
        Returns:
            Response from the community API
        """
        self._check_authentication()
        return self.connect.share_trading_setup(setup)
    
    def create_signal(self, 
                    symbol: str,
                    direction: str,
                    entry_price: float,
                    stop_loss: float,
                    take_profit: float,
                    timeframe: str,
                    description: str = "",
                    setup_type: str = "MT9EMA",
                    expiry_hours: Optional[int] = 24) -> Optional[TradingSignal]:
        """
        Create and share a trading signal.
        
        Args:
            symbol: Trading symbol
            direction: Trade direction ('buy' or 'sell')
            entry_price: Entry price level
            stop_loss: Stop loss level
            take_profit: Take profit level
            timeframe: Timeframe of the setup
            description: Description of the signal
            setup_type: Type of setup
            expiry_hours: Hours until signal expires
            
        Returns:
            TradingSignal object or None if failed
        """
        self._check_authentication()
        
        # Create the signal
        signal = self.signals.create_signal(
            user_id=self.user_id,
            username=self.username,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timeframe=timeframe,
            description=description,
            setup_type=setup_type,
            expiry_hours=expiry_hours
        )
        
        if signal:
            # Share the signal with the community
            self.signals.share_signal(signal, self.connect.api_key)
            logger.info(f"Created and shared signal for {symbol} {direction}")
        
        return signal
    
    def create_forum_post(self,
                        title: str,
                        content: str,
                        category: str,
                        tags: List[str] = None) -> Optional[ForumPost]:
        """
        Create a forum post.
        
        Args:
            title: Post title
            content: Post content
            category: Post category
            tags: List of tags
            
        Returns:
            ForumPost object or None if failed
        """
        self._check_authentication()
        
        post = self.forums.create_post(
            user_id=self.user_id,
            username=self.username,
            title=title,
            content=content,
            category=category,
            tags=tags
        )
        
        if post:
            logger.info(f"Created forum post: {title}")
        
        return post
    
    def get_community_overview(self) -> Dict[str, Any]:
        """
        Get an overview of community activity.
        
        Returns:
            Dictionary with community overview data
        """
        # Get trending topics
        trending_topics = self.forums.get_trending_topics(limit=5)
        
        # Get recent signals
        recent_signals = self.signals.get_signals(limit=5)
        
        # Get community performance stats
        performance = self.connect.get_community_performance(timeframe="week")
        
        # Get recent forum posts
        recent_posts = self.forums.get_recent_posts(limit=5)
        
        # Get leaderboard
        leaderboard = self.connect.get_leaderboard(timeframe="month", limit=5)
        
        # Get signal statistics
        signal_stats = self.signals.get_signal_statistics(days=30)
        
        # Combine into overview
        overview = {
            "trending_topics": trending_topics,
            "recent_signals": [s.to_dict() for s in recent_signals],
            "performance": performance,
            "recent_posts": [p.to_dict() for p in recent_posts],
            "leaderboard": leaderboard,
            "signal_stats": signal_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Retrieved community overview")
        return overview
    
    def get_user_profile(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a user's profile and activity data.
        
        Args:
            user_id: ID of the user (uses current user if None)
            
        Returns:
            Dictionary with user profile data
        """
        self._check_authentication()
        
        # Use current user if no user_id provided
        user_id = user_id or self.user_id
        
        # Get forum statistics
        forum_stats = self.forums.get_user_statistics(user_id)
        
        # Get performance data
        performance = self.signals.get_user_performance(user_id)
        
        # Get recent signals
        recent_signals = self.signals.get_signals(user_id=user_id, limit=5)
        
        # Get recent forum posts
        recent_posts = self.forums.get_posts(user_id=user_id, limit=5)
        
        # Combine into profile
        profile = {
            "user_id": user_id,
            "username": forum_stats.get("username", f"user_{user_id}"),
            "joined_date": forum_stats.get("joined_date"),
            "forum_stats": forum_stats,
            "performance": performance,
            "recent_signals": [s.to_dict() for s in recent_signals],
            "recent_posts": [p.to_dict() for p in recent_posts],
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Retrieved profile for user {user_id}")
        return profile
    
    def _check_authentication(self):
        """Check if user is authenticated and raise error if not."""
        if not self.is_authenticated:
            logger.warning("Not authenticated with community platform")
            raise ValueError("Authentication required. Please login first.")
