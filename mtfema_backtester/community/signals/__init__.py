"""
Signals module for MT 9 EMA Backtester.

This module provides functionality for creating, sharing, and managing trading signals.
"""

from mtfema_backtester.community.signals.subscription import (
    SignalSubscription, 
    get_subscription_manager,
    subscribe,
    unsubscribe,
    process_new_signal,
    get_user_subscriptions,
    get_pending_notifications
)

__all__ = [
    'SignalSubscription',
    'get_subscription_manager',
    'subscribe',
    'unsubscribe',
    'process_new_signal',
    'get_user_subscriptions',
    'get_pending_notifications'
]
