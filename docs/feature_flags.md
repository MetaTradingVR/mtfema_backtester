# Feature Flags System

## Overview

The MT 9 EMA Backtester implements a robust feature flagging system to enable gradual rollout of new functionality. This system allows for controlled feature releases, A/B testing, and the ability to quickly disable problematic features if needed.

## Key Capabilities

- **Gradual Rollout**: Release features to a percentage of users to gather feedback before full release
- **User Targeting**: Enable features for specific user groups (beta testers, admins, etc.)
- **Environment-Based Controls**: Override feature states through environment variables
- **Feature Dependencies**: Define dependencies between features to ensure proper feature enablement
- **Runtime Toggling**: Enable or disable features dynamically during runtime
- **Feature Categorization**: Tag features for easy filtering and management

## Using Feature Flags

### Checking if a Feature is Enabled

You can check if a feature is enabled in your code using the `is_feature_enabled` function:

```python
from mtfema_backtester.utils.feature_flags import is_feature_enabled

# Check if a feature is enabled for the current user
if is_feature_enabled("community.forums", user_id="user123"):
    # Show forums feature
    show_forums()
else:
    # Show placeholder or alternative
    show_forums_coming_soon()
```

### Feature-Gated Functions

You can use the `with_feature` decorator to conditionally execute functions based on feature flags:

```python
from mtfema_backtester.utils.feature_flags import with_feature

@with_feature("experimental.ai_signals")
def generate_ai_signals(market_data, user_id=None):
    # This function will only execute if the 'experimental.ai_signals' feature is enabled
    # for the given user_id
    # ...
    return signals
```

### Available Feature Flags

| Feature Name | Description | Default State | Category |
|--------------|-------------|---------------|----------|
| `community.forums` | Community discussion forums | Gradual (25%) | Community |
| `community.signals` | Trading signals system | Beta | Trading |
| `community.sharing` | Trading setup sharing | Beta | Trading |
| `community.profiles` | Enhanced user profiles | Gradual (50%) | Community |
| `security.2fa` | Two-factor authentication | On | Security |
| `performance.metrics_collection` | Anonymous usage metrics | On | Analytics |
| `experimental.ai_signals` | AI-generated trading signals | Admin | Experimental |

## Feature States

Features can be in one of the following states:

- **ON**: Enabled for all users
- **OFF**: Disabled for all users
- **GRADUAL**: Enabled for a percentage of users (based on user ID hash)
- **BETA**: Enabled only for beta users
- **ADMIN**: Enabled only for admin users
- **TARGETED**: Enabled only for specific users

## Environment Variable Overrides

You can override feature flags using environment variables with the prefix `MTFEMA_FEATURE_`:

```bash
# Enable forums for all users
export MTFEMA_FEATURE_COMMUNITY_FORUMS=on

# Disable metrics collection
export MTFEMA_FEATURE_PERFORMANCE_METRICS_COLLECTION=off

# Make AI signals available to beta users
export MTFEMA_FEATURE_EXPERIMENTAL_AI_SIGNALS=beta
```

## Managing Feature Flags

### Through Code

```python
from mtfema_backtester.utils.feature_flags import get_feature_flags, FeatureState

# Get the feature flags manager
feature_flags = get_feature_flags()

# Enable a feature for all users
feature_flags.set_override("community.forums", FeatureState.ON)

# Disable a feature
feature_flags.set_override("experimental.feature", FeatureState.OFF)

# Reset to default state
feature_flags.reset_override("community.forums")

# List all features with a specific tag
community_features = feature_flags.list_features(tag="community")
```

### Through Configuration File

You can define feature flags in a JSON configuration file:

```json
{
  "features": [
    {
      "name": "community.forums",
      "description": "Community discussion forums",
      "default_state": "gradual",
      "rollout_percentage": 25.0,
      "tags": ["community", "core"]
    },
    {
      "name": "community.signals",
      "description": "Trading signals system",
      "default_state": "beta",
      "tags": ["community", "trading"]
    }
  ],
  "admin_users": ["admin1", "admin2"],
  "beta_users": ["beta1", "beta2", "beta3"]
}
```

## Best Practices

1. **Feature Naming**: Use namespaced feature names (e.g., `category.feature_name`)
2. **Default to Off**: New features should generally default to Off or Gradual
3. **Testing**: Test both enabled and disabled states of features
4. **Dependencies**: Clearly define dependencies between features
5. **Documentation**: Keep the feature flags documentation updated
6. **Cleanup**: Remove feature flags for fully adopted features

## Implementation Details

The feature flags system is implemented in `mtfema_backtester/utils/feature_flags.py` using the following components:

- `FeatureState`: Enum defining possible feature states
- `FeatureFlag`: Class representing a single feature flag with metadata
- `FeatureFlagManager`: Singleton manager class for all feature flags
- Helper functions like `is_feature_enabled` and the `with_feature` decorator

The system uses a deterministic hashing algorithm for gradual rollout to ensure that the same user always gets the same experience. This provides consistency while still allowing for controlled feature releases. 