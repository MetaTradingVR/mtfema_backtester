"""
Community Features Package for MT 9 EMA Backtester.

This module provides functionality for social and collaborative
features, including signal sharing, subscriptions, reputation system,
and feature management.
"""

import logging
from mtfema_backtester.community.feature_flags import (
    FeatureFlags,
    get_feature_flags,
    is_feature_enabled
)
from .sharing import CommunityConnect
from .signals import SignalManager, TradingSignal
from .forums import ForumManager, ForumPost
from mtfema_backtester.utils.feature_flags import FeatureState

# Setup logger
logger = logging.getLogger(__name__)

# Check if community features are enabled
feature_flags = get_feature_flags()

FORUMS_ENABLED = feature_flags.is_enabled("community.forums")
SHARING_ENABLED = feature_flags.is_enabled("community.sharing")
SIGNALS_ENABLED = feature_flags.is_enabled("community.signals")
PROFILES_ENABLED = feature_flags.is_enabled("community.profiles")

if any([FORUMS_ENABLED, SHARING_ENABLED, SIGNALS_ENABLED, PROFILES_ENABLED]):
    logger.info("Community features are enabled")
else:
    logger.info("All community features are currently disabled")

__all__ = [
    'FeatureFlags',
    'get_feature_flags',
    'is_feature_enabled',
    'CommunityConnect',
    'SignalManager',
    'TradingSignal',
    'ForumManager',
    'ForumPost'
]
