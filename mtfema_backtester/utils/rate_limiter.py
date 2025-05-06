"""
Rate Limiting Utilities for MT 9 EMA Backtester.

This module provides rate limiting functionality for API requests to brokers
and other external services to prevent hitting API limits and ensure
graceful degradation under high load.
"""

import time
import logging
import threading
import queue
from typing import Dict, Any, Optional, Callable, List, Tuple
from dataclasses import dataclass
from functools import wraps

# Setup logger
logger = logging.getLogger(__name__)

@dataclass
class RateLimitRule:
    """Represents a rate limit rule with a time window and request limit."""
    
    # Maximum requests in time window
    requests: int
    
    # Time window in seconds
    window: float
    
    # Optional retry strategy (None, 'exponential', 'linear')
    retry_strategy: Optional[str] = 'exponential'
    
    # Maximum retries before giving up
    max_retries: int = 3
    
    # Base delay for retries (seconds)
    base_retry_delay: float = 1.0
    
    def __str__(self) -> str:
        return f"{self.requests} requests per {self.window}s"


class TokenBucket:
    """
    Token Bucket rate limiter implementation.
    
    This is a classic rate limiting algorithm that adds tokens to a bucket
    at a constant rate, and each request consumes a token. If no tokens
    are available, the request is either delayed or rejected.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize a token bucket.
        
        Args:
            capacity: Maximum number of tokens in the bucket
            refill_rate: Rate at which tokens are added (tokens/second)
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.RLock()
    
    def _refill(self) -> None:
        """Refill the bucket based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        
        if new_tokens > 0:
            self.tokens = min(self.capacity, self.tokens + new_tokens)
            self.last_refill = now
    
    def consume(self, tokens: int = 1, wait: bool = True) -> float:
        """
        Consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            wait: Whether to wait if tokens are not available
            
        Returns:
            Wait time in seconds (0 if no wait)
            
        Raises:
            ValueError: If tokens are not available and wait is False
        """
        with self.lock:
            self._refill()
            
            if self.tokens >= tokens:
                # Enough tokens available
                self.tokens -= tokens
                return 0.0
            
            if not wait:
                # Not enough tokens and not waiting
                raise ValueError("Rate limit exceeded")
            
            # Calculate wait time to get enough tokens
            deficit = tokens - self.tokens
            wait_time = deficit / self.refill_rate
            
            # Sleep for the required time
            time.sleep(wait_time)
            
            # Consume tokens after waiting
            self.tokens = 0
            return wait_time


class RateLimiter:
    """
    Rate limiter for API requests.
    
    Provides rate limiting with multiple strategies and rules.
    """
    
    def __init__(self):
        """Initialize the rate limiter."""
        self._limiters: Dict[str, TokenBucket] = {}
        self._limits: Dict[str, RateLimitRule] = {}
        self._lock = threading.RLock()
    
    def add_limit(self, key: str, rule: RateLimitRule) -> None:
        """
        Add a rate limit rule.
        
        Args:
            key: Unique identifier for the limit (e.g., 'tradovate.orders')
            rule: Rate limit rule to apply
        """
        with self._lock:
            self._limits[key] = rule
            
            # Create token bucket for the rule
            self._limiters[key] = TokenBucket(
                capacity=rule.requests,
                refill_rate=rule.requests / rule.window
            )
            
            logger.info(f"Added rate limit for {key}: {rule}")
    
    def remove_limit(self, key: str) -> bool:
        """
        Remove a rate limit rule.
        
        Args:
            key: Unique identifier for the limit
            
        Returns:
            True if the limit was removed, False if it didn't exist
        """
        with self._lock:
            if key in self._limits:
                del self._limits[key]
                del self._limiters[key]
                logger.info(f"Removed rate limit for {key}")
                return True
            return False
    
    def get_limit(self, key: str) -> Optional[RateLimitRule]:
        """
        Get a rate limit rule.
        
        Args:
            key: Unique identifier for the limit
            
        Returns:
            The rate limit rule, or None if not found
        """
        return self._limits.get(key)
    
    def check_limit(self, key: str, tokens: int = 1, wait: bool = True) -> float:
        """
        Check if a request is allowed under the rate limit.
        
        Args:
            key: Unique identifier for the limit
            tokens: Number of tokens to consume (usually 1 per request)
            wait: Whether to wait if the rate limit is exceeded
            
        Returns:
            Wait time in seconds (0 if no wait)
            
        Raises:
            ValueError: If the rate limit is exceeded and wait is False
            KeyError: If the rate limit key doesn't exist
        """
        with self._lock:
            if key not in self._limiters:
                raise KeyError(f"Rate limit not found: {key}")
            
            limiter = self._limiters[key]
            return limiter.consume(tokens, wait)
    
    def execute_with_retry(self, 
                         key: str, 
                         func: Callable, 
                         *args, 
                         **kwargs) -> Any:
        """
        Execute a function with rate limiting and retry logic.
        
        Args:
            key: Unique identifier for the limit
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the function call
            
        Raises:
            Exception: If all retries fail
        """
        if key not in self._limits:
            # No rate limit defined, just execute the function
            return func(*args, **kwargs)
        
        rule = self._limits[key]
        retry_count = 0
        last_error = None
        
        while retry_count <= rule.max_retries:
            try:
                # Wait if necessary to respect the rate limit
                wait_time = self.check_limit(key, wait=True)
                if wait_time > 0:
                    logger.debug(f"Rate limited request {key}, waiting {wait_time:.2f}s")
                
                # Execute the function
                return func(*args, **kwargs)
            
            except Exception as e:
                last_error = e
                retry_count += 1
                
                # Check if we should retry
                if retry_count > rule.max_retries or rule.retry_strategy is None:
                    logger.error(f"Request failed after {retry_count} attempts: {str(e)}")
                    raise
                
                # Calculate retry delay based on strategy
                if rule.retry_strategy == 'exponential':
                    delay = rule.base_retry_delay * (2 ** (retry_count - 1))
                elif rule.retry_strategy == 'linear':
                    delay = rule.base_retry_delay * retry_count
                else:
                    delay = rule.base_retry_delay
                
                logger.warning(f"Request failed, retrying in {delay:.2f}s ({retry_count}/{rule.max_retries}): {str(e)}")
                time.sleep(delay)
        
        # Should never reach here due to the raise in the loop
        raise last_error


# Global instance
rate_limiter = RateLimiter()

def get_rate_limiter() -> RateLimiter:
    """
    Get the global rate limiter instance.
    
    Returns:
        RateLimiter instance
    """
    return rate_limiter

def rate_limited(key: str, tokens: int = 1, wait: bool = True):
    """
    Decorator to apply rate limiting to a function.
    
    Args:
        key: Unique identifier for the limit
        tokens: Number of tokens to consume
        wait: Whether to wait if the rate limit is exceeded
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = get_rate_limiter()
            
            try:
                wait_time = limiter.check_limit(key, tokens, wait)
                if wait_time > 0:
                    logger.debug(f"Rate limited function {func.__name__}, waiting {wait_time:.2f}s")
            except KeyError:
                # No rate limit defined for this key
                logger.debug(f"No rate limit defined for {key}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def with_retries(key: str):
    """
    Decorator to apply rate limiting with retries to a function.
    
    Args:
        key: Unique identifier for the limit
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = get_rate_limiter()
            
            try:
                return limiter.execute_with_retry(key, func, *args, **kwargs)
            except KeyError:
                # No rate limit defined for this key
                logger.debug(f"No rate limit defined for {key}")
                return func(*args, **kwargs)
        return wrapper
    return decorator

# Default rate limits for brokers
def initialize_default_limits():
    """Initialize default rate limits for known brokers."""
    # Tradovate API limits
    rate_limiter.add_limit(
        'tradovate.market_data',
        RateLimitRule(requests=120, window=60.0, retry_strategy='exponential')
    )
    
    rate_limiter.add_limit(
        'tradovate.orders',
        RateLimitRule(requests=100, window=60.0, retry_strategy='exponential', max_retries=5)
    )
    
    rate_limiter.add_limit(
        'tradovate.account',
        RateLimitRule(requests=60, window=60.0, retry_strategy='linear')
    )
    
    # Rithmic API limits
    rate_limiter.add_limit(
        'rithmic.market_data',
        RateLimitRule(requests=150, window=60.0, retry_strategy='exponential')
    )
    
    rate_limiter.add_limit(
        'rithmic.orders',
        RateLimitRule(requests=120, window=60.0, retry_strategy='exponential', max_retries=5)
    )
    
    # General HTTP API limits
    rate_limiter.add_limit(
        'http.default',
        RateLimitRule(requests=30, window=60.0, retry_strategy='exponential')
    )
    
    logger.info("Initialized default rate limits for brokers")

# Initialize default limits when the module is imported
initialize_default_limits() 