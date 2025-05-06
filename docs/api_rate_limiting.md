# API Rate Limiting

## Overview

The MT 9 EMA Backtester implements a robust API rate limiting system to prevent hitting rate limits when interacting with broker APIs and other external services. This system ensures reliable communication with external services while handling errors gracefully.

## Key Capabilities

- **Token Bucket Algorithm**: Classic rate limiting algorithm that smoothly manages request rates
- **Broker-Specific Limits**: Predefined limits for supported brokers (Tradovate, Rithmic)
- **Retry Mechanisms**: Automatic retries with configurable strategies (exponential backoff, linear)
- **Wait or Fail Options**: Configure behavior when limits are reached (wait or fail immediately)
- **Decorator-Based Application**: Easy application to functions with decorators
- **Runtime Configuration**: Adjust rate limits dynamically during runtime

## Using API Rate Limiting

### Basic Rate Limiting

You can use the `rate_limited` decorator to apply rate limiting to any function:

```python
from mtfema_backtester.utils.rate_limiter import rate_limited

@rate_limited(key="tradovate.market_data")
def get_market_data(symbol):
    # This function will be rate limited according to Tradovate's market data limits
    # ...
    return data
```

### Rate Limiting with Retries

For functions that need both rate limiting and automatic retries on failure:

```python
from mtfema_backtester.utils.rate_limiter import with_retries

@with_retries(key="tradovate.orders")
def place_order(order_data):
    # This function will be rate limited and will automatically retry on failure
    # using the retry strategy defined for Tradovate orders
    # ...
    return order_confirmation
```

### Manual Rate Limiting

For more complex scenarios, you can use the rate limiter directly:

```python
from mtfema_backtester.utils.rate_limiter import get_rate_limiter

def complex_operation():
    limiter = get_rate_limiter()
    
    # Check if we can proceed
    try:
        # Will wait if necessary to respect the limit
        wait_time = limiter.check_limit("tradovate.orders", wait=True)
        if wait_time > 0:
            print(f"Had to wait {wait_time:.2f}s due to rate limiting")
        
        # Perform the operation
        # ...
    except KeyError:
        # No rate limit defined for this key
        # ...
```

### Execute with Retry Logic

For even more control, you can use the execute_with_retry method:

```python
from mtfema_backtester.utils.rate_limiter import get_rate_limiter

def complex_operation_with_retry():
    limiter = get_rate_limiter()
    
    # Define the function to execute
    def perform_api_call(param1, param2):
        # ...
        return result
    
    # Execute with rate limiting and retry logic
    try:
        result = limiter.execute_with_retry(
            "tradovate.orders", 
            perform_api_call, 
            "param1_value", 
            param2="param2_value"
        )
        return result
    except Exception as e:
        # All retries failed
        # ...
```

## Default Rate Limits

The following rate limits are predefined in the system:

| API Key | Requests | Window (seconds) | Retry Strategy | Max Retries |
|---------|----------|------------------|----------------|-------------|
| `tradovate.market_data` | 120 | 60 | exponential | 3 |
| `tradovate.orders` | 100 | 60 | exponential | 5 |
| `tradovate.account` | 60 | 60 | linear | 3 |
| `rithmic.market_data` | 150 | 60 | exponential | 3 |
| `rithmic.orders` | 120 | 60 | exponential | 5 |
| `http.default` | 30 | 60 | exponential | 3 |

## Configuring Rate Limits

### Adding Custom Rate Limits

```python
from mtfema_backtester.utils.rate_limiter import get_rate_limiter, RateLimitRule

# Get the rate limiter
limiter = get_rate_limiter()

# Add a custom rate limit
limiter.add_limit(
    "custom.api",
    RateLimitRule(
        requests=50,         # 50 requests
        window=60.0,         # per 60 seconds
        retry_strategy="exponential",  # exponential backoff
        max_retries=3,       # retry up to 3 times
        base_retry_delay=2.0 # start with 2 second delay
    )
)
```

### Removing a Rate Limit

```python
limiter = get_rate_limiter()
limiter.remove_limit("custom.api")
```

## Retry Strategies

The system supports the following retry strategies:

- **exponential**: Each retry waits `base_delay * (2 ^ (retry_count - 1))` seconds
- **linear**: Each retry waits `base_delay * retry_count` seconds
- **None**: No retries, fail immediately after the first failure

## Configuration Best Practices

1. **Be Conservative**: Set limits below the actual API limits to account for other processes
2. **Adjust Base Delays**: For critical operations, use smaller base delays; for less critical ones, use larger delays
3. **Monitor Usage**: Keep track of actual API usage to optimize limits
4. **Test Failure Scenarios**: Ensure your application handles rate limiting and retries correctly

## Implementation Details

The rate limiting system is implemented in `mtfema_backtester/utils/rate_limiter.py` using the following components:

- `TokenBucket`: Class implementing the token bucket algorithm
- `RateLimitRule`: Data class defining a rate limit rule
- `RateLimiter`: Main class managing rate limits and applying them
- Helper decorators: `rate_limited` and `with_retries`

The system is thread-safe and can be used across multiple threads without issues. 