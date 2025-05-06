# Anonymous Metrics Collection

This document outlines the metrics collection system in the MT 9 EMA Backtester, designed to gather anonymous usage data that helps improve the application while respecting user privacy.

## Overview

The metrics collection system provides valuable insights into how users interact with the MT 9 EMA Backtester. This data helps identify which features are most valuable, where users encounter difficulties, and how to prioritize future development efforts.

All metrics are:
- **Anonymous**: No personally identifiable information is ever collected
- **Opt-out**: Users can disable metrics collection at any time
- **Transparent**: This documentation details exactly what is collected and why
- **Secure**: Data is stored securely and only used for application improvement

## What We Collect

The metrics collection system captures the following types of data:

### Feature Usage Metrics

These metrics help understand which features are most valuable to users:

- **Feature Activation**: Which features are used and how often
- **Feature Flow**: Sequences of features used together
- **Configuration Preferences**: What settings and configurations are most common
- **Time Spent**: How long users engage with different features

### Performance Metrics

These metrics help identify and resolve performance issues:

- **Operation Duration**: How long various operations take to complete
- **Resource Utilization**: CPU, memory, and network usage patterns
- **Bottlenecks**: Identification of slow operations
- **Error Rates**: Frequency and types of errors encountered

### User Experience Metrics

These metrics help improve the overall user experience:

- **Navigation Patterns**: How users move through the application
- **Screen Resolution and Device Info**: Help optimize the UI for different devices
- **Interaction Patterns**: How users interact with controls and visualizations
- **Session Length**: How long users typically use the application

## How Metrics Are Collected

The metrics collection system works as follows:

1. **Event Generation**: When a user performs an action, an anonymized event is generated
2. **Local Buffering**: Events are stored locally in memory
3. **Periodic Submission**: Events are periodically sent to storage (every 5 minutes or 100 events)
4. **Aggregation**: Events are aggregated for analysis
5. **Insights Generation**: Patterns and insights are extracted to guide improvements

## Privacy Protections

We've implemented several privacy protections:

### User Anonymization

All identifiable information is removed:

```python
# Example of how user identifiers are anonymized
def get_anonymous_user_id(self) -> str:
    # Use machine-specific but non-PII information
    machine_info = [
        os.getenv("COMPUTERNAME", ""),
        os.getenv("USERNAME", ""),
        str(uuid.getnode())  # MAC address
    ]
    
    # Hash the information to create an anonymous ID
    hash_input = ":".join(machine_info).encode("utf-8")
    return hashlib.sha256(hash_input).hexdigest()
```

### Opt-Out System

Users can opt out of metrics collection at any time:

1. **Environment Variable**: Set `MTFEMA_METRICS_OPT_OUT=true`
2. **Configuration File**: Set `metrics_opt_out: true` in the config file
3. **API**: Call `metrics_collector.opt_out()` in code
4. **UI**: Toggle in the application settings (recommended)

### Data Minimization

We follow data minimization principles:

- Only collect what's necessary for improvement
- Automatically exclude sensitive data
- Apply automatic data retention policies

## Implementation for Developers

### Tracking Events

To track usage of a feature:

```python
from mtfema_backtester.utils.metrics_collector import track_feature_usage, MetricCategory, track_event

# Simple feature usage tracking
track_feature_usage("backtest_run", {"timeframes": "5m,15m,1h"})

# Tracking performance metrics
track_performance("data_loading", 1250.5)  # duration in ms

# Custom event tracking
track_event(
    category=MetricCategory.STRATEGY,
    name="strategy_parameter_changed",
    properties={"parameter": "ema_period", "value": 9}
)
```

### Using the Metrics Decorator

For automatic tracking of feature usage and performance:

```python
from mtfema_backtester.utils.metrics_collector import with_metrics

@with_metrics("run_backtest", include_duration=True)
def run_backtest(symbol, timeframes, start_date, end_date):
    # Implementation
    return results
```

### Checking Opt-Out Status

Always respect the user's preference:

```python
from mtfema_backtester.utils.metrics_collector import get_metrics_collector

def my_function():
    metrics = get_metrics_collector()
    
    # Check if user has opted out
    if not metrics.is_opted_out():
        # Perform metrics collection
        metrics.track_event(...)
```

## FAQ

### Is my trading data being collected?

No. We never collect specific trading data, strategy parameters, or backtest results. We only collect anonymous usage patterns, not the actual content you're working with.

### Can I see what data has been collected?

Yes. You can view the local metrics storage at `~/.mtfema/metrics/` to see exactly what has been collected before it's transmitted.

### Does metrics collection affect performance?

The metrics collection system is designed to have minimal impact on performance. Events are buffered in memory and only periodically saved or transmitted.

### How can I completely disable metrics?

Set the environment variable `MTFEMA_METRICS_OPT_OUT=true` before starting the application, or call `metrics_collector.opt_out()` in your code.

## Data Categories Reference

For developers, here's the complete list of metric categories:

| Category | Purpose | Example Events |
|----------|---------|---------------|
| `PERFORMANCE` | Track timing and resource usage | `data_loading_completed`, `backtest_duration` |
| `FEATURE_USAGE` | Track feature utilization | `feature_activated`, `chart_type_selected` |
| `USER_ENGAGEMENT` | Track overall engagement | `session_started`, `tutorial_completed` |
| `ERROR` | Track errors and exceptions | `error_occurred`, `api_request_failed` |
| `STRATEGY` | Track strategy-related actions | `strategy_created`, `parameter_changed` |
| `BACKTEST` | Track backtest operations | `backtest_started`, `results_exported` |
| `COMMUNITY` | Track community interactions | `post_created`, `setup_shared` |
| `SYSTEM` | Track system operations | `system_initialized`, `update_checked` |

## Metrics Collection Principles

Our metrics collection adheres to these core principles:

1. **Privacy by Design**
   - Collect only what's necessary
   - Anonymize data whenever possible
   - Provide transparent opt-out options

2. **Value-Driven Collection**
   - Each metric must have a clear purpose
   - Metrics should inform actionable decisions
   - Regular review of metric relevance

3. **User Transparency**
   - Clear communication about what's collected
   - Simple privacy controls
   - User access to their own data

## Key Metrics Categories

### 1. Feature Usage Metrics

These metrics help us understand which features are most valuable to users.

| Metric | Description | Purpose | Privacy Level |
|--------|-------------|---------|--------------|
| Feature Access Count | Number of times each feature is accessed | Identify popular features | Low |
| Time Spent in Feature | Duration of active usage per feature | Understand engagement depth | Medium |
| Feature Completion Rate | % of feature flows completed | Identify friction points | Medium |
| Feature Usage Pattern | Order and combinations of features used | Optimize feature placement | Medium |
| Feature Abandonment Points | Where users exit feature flows | Identify UX issues | Medium |

### 2. Community Engagement Metrics

These metrics help us understand community dynamics and value.

| Metric | Description | Purpose | Privacy Level |
|--------|-------------|---------|--------------|
| Content Creation Rate | Volume of created content by type | Measure contribution levels | Low |
| Content Interaction Rate | Likes, comments, shares | Measure content quality | Low |
| Community DAU/MAU | Daily/Monthly active users | Measure ongoing engagement | Low |
| User Retention | Return frequency after first use | Measure sustained value | Medium |
| Social Network Growth | Follows, connections made | Measure community building | Medium |

### 3. Trading Signal Metrics

These metrics help us understand signal value and usage.

| Metric | Description | Purpose | Privacy Level |
|--------|-------------|---------|--------------|
| Signal Creation Count | Number of signals created | Measure feature adoption | Low |
| Signal Success Rate | % of signals with profitable outcome | Measure signal quality | Medium |
| Signal Follow Rate | % of signals followed by others | Measure trust | Medium |
| Time to Signal Execution | Delay between creation and execution | Measure timeliness | Medium |
| Most Common Symbols | Frequently used trading instruments | Identify popular markets | Low |

### 4. System Performance Metrics

These metrics help us optimize platform performance.

| Metric | Description | Purpose | Privacy Level |
|--------|-------------|---------|--------------|
| Page Load Time | Time to interactive for key pages | Identify performance issues | Low |
| API Response Time | Backend processing time | Identify bottlenecks | Low |
| Error Rate | Frequency of system errors | Identify reliability issues | Low |
| Resource Utilization | CPU, memory, network usage | Capacity planning | Low |
| Operation Completion Time | Time for key operations | Identify optimization targets | Low |

## Implementation Strategy

### Technical Implementation

We implement metrics collection using a layered approach:

```python
# Simple example of our metrics tracking system
import time
import uuid
from typing import Dict, Any, Optional
import json
import hashlib
import os

class MetricsCollector:
    def __init__(self, 
                 app_id: str, 
                 collect_enabled: bool = True,
                 anonymize: bool = True):
        self.app_id = app_id
        self.collect_enabled = collect_enabled
        self.anonymize = anonymize
        self.session_id = str(uuid.uuid4())
        self.metrics_buffer = []
        self.buffer_size_limit = 50
        self.metrics_dir = "data/metrics"
        os.makedirs(self.metrics_dir, exist_ok=True)
    
    def track_event(self, 
                    event_name: str, 
                    properties: Dict[str, Any] = None,
                    user_id: Optional[str] = None) -> None:
        """Track a specific event with properties"""
        if not self.collect_enabled:
            return
            
        # Skip tracking if user has opted out
        if self._is_user_opted_out(user_id):
            return
            
        properties = properties or {}
        
        # Create event data
        event_data = {
            "event": event_name,
            "timestamp": int(time.time()),
            "session_id": self.session_id,
            "properties": properties
        }
        
        # Add anonymized user ID if available
        if user_id and self.anonymize:
            event_data["user_id"] = self._anonymize_user_id(user_id)
        elif user_id:
            event_data["user_id"] = user_id
            
        # Add to buffer
        self.metrics_buffer.append(event_data)
        
        # Flush if buffer is full
        if len(self.metrics_buffer) >= self.buffer_size_limit:
            self.flush()
    
    def track_feature_usage(self, 
                          feature_name: str, 
                          action: str,
                          user_id: Optional[str] = None,
                          properties: Dict[str, Any] = None) -> None:
        """Track feature usage with standardized format"""
        props = properties or {}
        props.update({
            "feature": feature_name,
            "action": action
        })
        self.track_event(
            event_name="feature_usage",
            properties=props,
            user_id=user_id
        )
    
    def start_feature_timer(self, feature_name: str) -> int:
        """Start timing a feature usage"""
        return int(time.time() * 1000)
    
    def end_feature_timer(self, 
                         feature_name: str, 
                         start_time: int,
                         user_id: Optional[str] = None,
                         was_completed: bool = True) -> None:
        """End timing and record feature usage duration"""
        end_time = int(time.time() * 1000)
        duration_ms = end_time - start_time
        
        self.track_feature_usage(
            feature_name=feature_name,
            action="usage_time",
            user_id=user_id,
            properties={
                "duration_ms": duration_ms,
                "completed": was_completed
            }
        )
    
    def flush(self) -> None:
        """Flush metrics to storage"""
        if not self.metrics_buffer:
            return
            
        timestamp = int(time.time())
        filename = f"{self.metrics_dir}/metrics_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.metrics_buffer, f)
            
        self.metrics_buffer = []
    
    def _anonymize_user_id(self, user_id: str) -> str:
        """Create anonymized hash of user ID"""
        # Salt with app ID to prevent cross-app correlation
        salted = f"{user_id}:{self.app_id}"
        return hashlib.sha256(salted.encode()).hexdigest()
    
    def _is_user_opted_out(self, user_id: Optional[str]) -> bool:
        """Check if user has opted out of metrics collection"""
        # Implementation would check against a database of opt-outs
        # This is a placeholder implementation
        return False
