# Reputation System

This document outlines the reputation system for the MT 9 EMA Backtester community, which tracks user contributions, awards points and badges, and generates leaderboards.

## Overview

The reputation system provides a gamified community experience that incentivizes quality contributions, engagement, and knowledge sharing. Users earn reputation points for various actions, level up as they accumulate points, and earn badges for specific achievements.

## Key Features

### Points System

Users earn reputation points for the following actions:

| Action | Points | Description |
|--------|--------|-------------|
| Forum Post Creation | 10 | Creating a new forum post |
| Forum Post Like | 1 | Liking another user's post |
| Forum Post Liked | 5 | Having your post liked by another user |
| Forum Solution | 25 | Having your post marked as a solution |
| Signal Creation | 15 | Creating a new trading signal |
| Signal Success | 20 | When a signal you created is successful |
| Signal Followed | 5 | When another user follows your signal |
| Setup Share | 15 | Sharing a trading setup |
| Setup Liked | 5 | Having your setup liked by another user |
| Backtest Share | 10 | Sharing a backtest result |
| Daily Login | 2 | Logging in daily |
| Profile Completion | 5 | Completing your user profile |

### Levels System

Users progress through levels as they accumulate reputation points:

| Level | Points Required |
|-------|----------------|
| 1 | 0 |
| 2 | 100 |
| 3 | 300 |
| 4 | 600 |
| 5 | 1,000 |
| 6 | 1,500 |
| 7 | 2,100 |
| 8 | 3,000 |
| 9 | 4,000 |
| 10 | 5,500 |
| 11 | 7,500 |
| 12 | 10,000 |

### Badges System

Users earn badges for specific achievements:

#### Forum Badges
- **Forum Novice** (📝): Created your first forum post
- **Forum Contributor** (✍️): Created 10 forum posts
- **Forum Expert** (🖋️): Created 50 forum posts
- **Helpful Advisor** (💡): Your post was marked as a solution 5 times

#### Signal Badges
- **Signal Provider** (📊): Shared your first trading signal
- **Signal Master** (📈): Shared 20 successful trading signals
- **Popular Trader** (👥): Your signals were followed 50 times

#### Setup Badges
- **Setup Sharer** (📋): Shared your first trading setup
- **Setup Guru** (👍): Your setups received 100 likes

#### Reputation Badges
- **Bronze Trader** (🥉): Reached 100 reputation points
- **Silver Trader** (🥈): Reached 500 reputation points
- **Gold Trader** (🥇): Reached 1,000 reputation points
- **Diamond Trader** (💎): Reached 5,000 reputation points

### Leaderboards

The system generates leaderboards in multiple categories:

- **Reputation Leaderboard**: Overall reputation points
- **Signals Leaderboard**: Performance in creating and sharing successful signals
- **Forum Leaderboard**: Contribution to community discussions

Leaderboards can be filtered by timeframe (daily, weekly, monthly, all-time).

## How to Use the Reputation System

### Basic Usage

To award points to a user for an action:

```python
from mtfema_backtester.community.reputation import award_points, ActionType

# Award points for creating a forum post
award_points(
    user_id="user123",
    action_type=ActionType.FORUM_POST_CREATE.value,
    context={"post_id": "post456"}
)
```

### Getting User Reputation Data

To get a user's current reputation status:

```python
from mtfema_backtester.community.reputation import get_user_reputation

# Get user's reputation data
reputation_data = get_user_reputation("user123")

print(f"Points: {reputation_data['points']}")
print(f"Level: {reputation_data['level']}")
print(f"Rank: {reputation_data['rank']}")
```

### Getting User Badges

To get the badges a user has earned:

```python
from mtfema_backtester.community.reputation import get_user_badges

# Get user's badges
badges = get_user_badges("user123")

for badge in badges:
    print(f"{badge['icon']} {badge['name']}: {badge['description']}")
```

### Generating Leaderboards

To generate a leaderboard:

```python
from mtfema_backtester.community.reputation import generate_leaderboard

# Generate a reputation leaderboard
reputation_leaderboard = generate_leaderboard(
    category="reputation",
    timeframe="month",
    limit=10
)

# Generate a signals leaderboard
signals_leaderboard = generate_leaderboard(
    category="signals",
    timeframe="all_time",
    limit=5
)
```

## Integration with Other Community Features

The reputation system integrates with other community features:

### Forums Integration

When a user creates a forum post, likes a post, or has their post marked as a solution, the forums system automatically awards reputation points:

```python
# Example from forums.py
from mtfema_backtester.community.reputation import award_points, ActionType

def create_post(user_id, title, content, category):
    # Create the post...
    
    # Award points for creating a post
    award_points(user_id, ActionType.FORUM_POST_CREATE.value, {"post_id": post_id})
    
    return post
```

### Signals Integration

When a user creates a signal or has their signal followed, the signals system awards reputation points:

```python
# Example from signals.py
from mtfema_backtester.community.reputation import award_points, ActionType

def create_signal(user_id, symbol, direction, entry_price, stop_loss):
    # Create the signal...
    
    # Award points for creating a signal
    award_points(user_id, ActionType.SIGNAL_CREATE.value, {"signal_id": signal_id})
    
    return signal
```

## Technical Implementation

The reputation system is implemented as a singleton with thread-safety to ensure consistent data across the application. Data is persisted to disk for reliability across application restarts.

### Data Storage

Reputation data is stored in JSON files:

- `user_reputation.json`: Contains user points, levels, badges, and action counts
- `action_history.json`: Contains detailed history of user actions

These files are located in the `.mtfema/community/reputation` directory by default.

## Future Enhancements

Planned enhancements to the reputation system include:

1. **Achievement Notifications**: Real-time notifications when users earn badges or level up
2. **Advanced Analytics**: Detailed analytics on user contributions and community engagement
3. **Custom Badges**: Allow community administrators to create custom badges
4. **Badge Showcasing**: Allow users to showcase selected badges on their profile
5. **Automated Challenges**: Time-limited challenges with special badges and rewards 