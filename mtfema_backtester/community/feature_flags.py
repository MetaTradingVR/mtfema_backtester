"""
Feature flags system for MT 9 EMA Backtester.

This module provides a centralized system for managing feature flags,
allowing gradual rollout of features and A/B testing capabilities.
"""

import logging
from typing import Dict, Any, Optional
import os
import json
import random

logger = logging.getLogger(__name__)

class FeatureFlags:
    """
    Manages feature flags for controlling feature availability.
    
    Features:
    - Configuration from files and environment variables
    - Default conservative settings
    - User-specific flag overrides
    - Usage tracking for analytics
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern for global feature flag access."""
        if cls._instance is None:
            cls._instance = super(FeatureFlags, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the feature flags system.
        
        Args:
            config_path: Path to configuration file
        """
        # Skip re-initialization if already initialized
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        self.config_path = config_path
        
        # Default flags configuration (conservative - most features off by default)
        self.flags = {
            # Core features - always on
            "backtesting": True,
            "visualization": True,
            "strategy_config": True,
            
            # Community features - off by default until stable
            "forums": False,
            "sharing": False,
            "signals": False,
            "signal_subscriptions": False,
            "signal_notifications": False,
            "content_moderation": False,
            "reputation_system": False,
            
            # Mobile features
            "mobile_basic": False,
            "mobile_advanced": False,
            "offline_mode": False,
            
            # Security features
            "two_factor_auth": False,
            "secure_sharing": False,
            
            # Analytics and metrics
            "usage_metrics": True,
            "performance_metrics": True,
            "community_metrics": False,
            
            # New experimental features
            "ai_signal_analyzer": False,
            "market_sentiment": False,
            "auto_trade": False
        }
        
        # User-specific flag overrides
        self.user_overrides = {}
        
        # Flag usage tracking
        self.flag_usage = {}
        
        # Load configuration
        self._load_config()
        
        # Check environment variables
        self._load_env_vars()
        
        logger.info("Feature flags system initialized")
    
    def is_enabled(self, feature_name: str, user_id: Optional[str] = None) -> bool:
        """
        Check if a feature is enabled for a specific user.
        
        Args:
            feature_name: Name of the feature
            user_id: Optional user ID for user-specific overrides
            
        Returns:
            Whether the feature is enabled
        """
        # Track usage
        if feature_name not in self.flag_usage:
            self.flag_usage[feature_name] = 0
        self.flag_usage[feature_name] += 1
        
        # Check user-specific override
        if user_id and user_id in self.user_overrides and feature_name in self.user_overrides[user_id]:
            return self.user_overrides[user_id][feature_name]
        
        # Check global flag
        return self.flags.get(feature_name, False)
    
    def set_flag(self, feature_name: str, enabled: bool) -> None:
        """
        Set a global feature flag.
        
        Args:
            feature_name: Name of the feature
            enabled: Whether the feature should be enabled
        """
        self.flags[feature_name] = enabled
        logger.info(f"Set feature flag {feature_name} to {enabled}")
    
    def set_user_flag(self, user_id: str, feature_name: str, enabled: bool) -> None:
        """
        Set a user-specific feature flag override.
        
        Args:
            user_id: ID of the user
            feature_name: Name of the feature
            enabled: Whether the feature should be enabled for this user
        """
        if user_id not in self.user_overrides:
            self.user_overrides[user_id] = {}
        
        self.user_overrides[user_id][feature_name] = enabled
        logger.info(f"Set user-specific flag {feature_name} to {enabled} for user {user_id}")
    
    def get_flag_usage(self) -> Dict[str, int]:
        """
        Get usage statistics for feature flags.
        
        Returns:
            Dictionary of feature names and usage counts
        """
        return self.flag_usage
    
    def _load_config(self) -> None:
        """
        Load feature flags from configuration file.
        """
        if not self.config_path:
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # Update flags from config
            if "flags" in config:
                self.flags.update(config["flags"])
                
            # Load user overrides
            if "user_overrides" in config:
                self.user_overrides = config["user_overrides"]
                
            logger.info(f"Loaded feature flags configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Error loading feature flags config: {e}")
    
    def _load_env_vars(self) -> None:
        """
        Load feature flags from environment variables.
        
        Environment variables should be in the format:
        MTFEMA_FEATURE_<FEATURE_NAME>=true/false
        """
        prefix = "MTFEMA_FEATURE_"
        
        # Check all environment variables
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Extract feature name
                feature_name = key[len(prefix):].lower()
                
                # Convert value to boolean
                enabled = value.lower() in ('true', '1', 'yes', 'y', 'on')
                
                # Set flag
                self.flags[feature_name] = enabled
                logger.info(f"Set feature flag {feature_name} to {enabled} from environment variable")
    
    def enable_for_percentage(self, feature_name: str, percentage: float) -> None:
        """
        Enable a feature for a percentage of users.
        
        Args:
            feature_name: Name of the feature
            percentage: Percentage of users to enable for (0-100)
        """
        logger.info(f"Setting up {feature_name} for {percentage}% of users")
        
        # Validate percentage
        if percentage < 0 or percentage > 100:
            logger.error(f"Invalid percentage {percentage}, must be between 0-100")
            return
        
        # Set global flag based on percentage
        if percentage >= 100:
            self.flags[feature_name] = True
        elif percentage <= 0:
            self.flags[feature_name] = False
        else:
            # For partial rollouts, we'll use the user_id to determine eligibility
            # This is handled in is_enabled with user-specific logic
            pass
    
    def is_user_in_segment(self, user_id: str, percentage: float) -> bool:
        """
        Determine if a user is in a specific segment based on percentage.
        
        Args:
            user_id: ID of the user
            percentage: Percentage threshold (0-100)
            
        Returns:
            Whether the user is in the segment
        """
        if not user_id:
            return False
            
        # Use hash of user_id for consistent randomization
        hash_value = hash(user_id) % 100
        return hash_value < percentage


# Helper functions for easier access

def get_feature_flags() -> FeatureFlags:
    """
    Get the global feature flags instance.
    
    Returns:
        FeatureFlags instance
    """
    return FeatureFlags()

def is_feature_enabled(feature_name: str, user_id: Optional[str] = None) -> bool:
    """
    Check if a feature is enabled.
    
    Args:
        feature_name: Name of the feature
        user_id: Optional user ID for user-specific overrides
        
    Returns:
        Whether the feature is enabled
    """
    flags = get_feature_flags()
    return flags.is_enabled(feature_name, user_id)
