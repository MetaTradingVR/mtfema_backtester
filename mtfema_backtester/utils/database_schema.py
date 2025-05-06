"""
Database Schema Design for MT 9 EMA Backtester Community Features.

This module defines the database schema design for community features
of the MT 9 EMA Backtester, optimized for common query patterns and
designed for scalability from dozens to thousands of users.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Set, Optional, Union
import logging

# Setup logger
logger = logging.getLogger(__name__)

class UserStatus(Enum):
    """Status of a user account."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    PENDING_VERIFICATION = "pending_verification"


class ContentStatus(Enum):
    """Status of user-generated content."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"
    PENDING_MODERATION = "pending_moderation"
    REJECTED = "rejected"


class Schema:
    """
    Database schema definitions for the MT 9 EMA Backtester.
    
    Provides a structured schema definition optimized for:
    1. Common query patterns in the application
    2. Scaling from dozens to thousands of users
    3. Supporting community features like forums, trading setup sharing, and signals
    """
    
    # User-related tables
    users = {
        "table_name": "users",
        "primary_key": "user_id",
        "columns": {
            "user_id": {"type": "UUID", "description": "Unique identifier for the user"},
            "username": {"type": "VARCHAR(50)", "description": "Unique username", "index": True},
            "email": {"type": "VARCHAR(255)", "description": "User's email address", "index": True},
            "password_hash": {"type": "VARCHAR(255)", "description": "Hashed password"},
            "salt": {"type": "VARCHAR(255)", "description": "Salt for password hashing"},
            "status": {"type": "VARCHAR(20)", "description": "User account status (active, suspended, etc.)"},
            "email_verified": {"type": "BOOLEAN", "description": "Whether email has been verified"},
            "created_at": {"type": "TIMESTAMP", "description": "When the user account was created"},
            "updated_at": {"type": "TIMESTAMP", "description": "When the user account was last updated"},
            "last_login_at": {"type": "TIMESTAMP", "description": "When the user last logged in"},
            "profile_picture_url": {"type": "VARCHAR(255)", "description": "URL to profile picture"},
            "time_zone": {"type": "VARCHAR(50)", "description": "User's time zone"}
        },
        "indexes": [
            {"columns": ["username"], "unique": True},
            {"columns": ["email"], "unique": True},
            {"columns": ["created_at"]}
        ]
    }
    
    user_profiles = {
        "table_name": "user_profiles",
        "primary_key": "user_id",
        "columns": {
            "user_id": {"type": "UUID", "description": "Foreign key to users table", "foreign_key": "users.user_id"},
            "display_name": {"type": "VARCHAR(100)", "description": "User's display name"},
            "bio": {"type": "TEXT", "description": "User's biography"},
            "location": {"type": "VARCHAR(100)", "description": "User's location"},
            "website": {"type": "VARCHAR(255)", "description": "User's website"},
            "trading_experience": {"type": "VARCHAR(20)", "description": "User's trading experience level"},
            "preferred_markets": {"type": "VARCHAR(255)", "description": "Comma-separated list of preferred markets"},
            "preferred_timeframes": {"type": "VARCHAR(255)", "description": "Comma-separated list of preferred timeframes"},
            "social_links": {"type": "JSONB", "description": "JSON object containing social media links"},
            "privacy_settings": {"type": "JSONB", "description": "JSON object containing privacy preferences"},
            "created_at": {"type": "TIMESTAMP", "description": "When the profile was created"},
            "updated_at": {"type": "TIMESTAMP", "description": "When the profile was last updated"}
        },
        "indexes": [
            {"columns": ["user_id"], "unique": True}
        ]
    }
    
    user_roles = {
        "table_name": "user_roles",
        "primary_key": ["user_id", "role"],
        "columns": {
            "user_id": {"type": "UUID", "description": "Foreign key to users table", "foreign_key": "users.user_id"},
            "role": {"type": "VARCHAR(20)", "description": "Role name (admin, moderator, premium, etc.)"},
            "granted_at": {"type": "TIMESTAMP", "description": "When the role was granted"},
            "granted_by": {"type": "UUID", "description": "Who granted the role", "foreign_key": "users.user_id"},
            "expires_at": {"type": "TIMESTAMP", "description": "When the role expires (null for permanent)"}
        },
        "indexes": [
            {"columns": ["user_id", "role"], "unique": True},
            {"columns": ["role"]}
        ]
    }
    
    user_achievements = {
        "table_name": "user_achievements",
        "primary_key": ["user_id", "achievement_id"],
        "columns": {
            "user_id": {"type": "UUID", "description": "Foreign key to users table", "foreign_key": "users.user_id"},
            "achievement_id": {"type": "VARCHAR(50)", "description": "Unique identifier for the achievement"},
            "achieved_at": {"type": "TIMESTAMP", "description": "When the achievement was earned"},
            "progress": {"type": "INTEGER", "description": "Progress towards achievement (if applicable)"},
            "displayed": {"type": "BOOLEAN", "description": "Whether to display on profile"}
        },
        "indexes": [
            {"columns": ["user_id", "achievement_id"], "unique": True},
            {"columns": ["achievement_id"]}
        ]
    }
    
    # Forum-related tables
    forum_categories = {
        "table_name": "forum_categories",
        "primary_key": "category_id",
        "columns": {
            "category_id": {"type": "UUID", "description": "Unique identifier for the category"},
            "name": {"type": "VARCHAR(100)", "description": "Category name"},
            "description": {"type": "TEXT", "description": "Category description"},
            "slug": {"type": "VARCHAR(100)", "description": "URL-friendly category identifier", "index": True},
            "parent_category_id": {"type": "UUID", "description": "Parent category ID (null for top-level)", "foreign_key": "forum_categories.category_id"},
            "position": {"type": "INTEGER", "description": "Display order position"},
            "created_at": {"type": "TIMESTAMP", "description": "When the category was created"},
            "updated_at": {"type": "TIMESTAMP", "description": "When the category was last updated"},
            "is_private": {"type": "BOOLEAN", "description": "Whether the category is for specific roles only"},
            "icon_url": {"type": "VARCHAR(255)", "description": "URL to category icon"}
        },
        "indexes": [
            {"columns": ["slug"], "unique": True},
            {"columns": ["parent_category_id"]},
            {"columns": ["position"]}
        ]
    }
    
    forum_topics = {
        "table_name": "forum_topics",
        "primary_key": "topic_id",
        "columns": {
            "topic_id": {"type": "UUID", "description": "Unique identifier for the topic"},
            "category_id": {"type": "UUID", "description": "Foreign key to forum_categories table", "foreign_key": "forum_categories.category_id"},
            "user_id": {"type": "UUID", "description": "Foreign key to users table", "foreign_key": "users.user_id"},
            "title": {"type": "VARCHAR(255)", "description": "Topic title"},
            "slug": {"type": "VARCHAR(255)", "description": "URL-friendly topic identifier", "index": True},
            "status": {"type": "VARCHAR(20)", "description": "Topic status (published, archived, etc.)"},
            "is_pinned": {"type": "BOOLEAN", "description": "Whether the topic is pinned to the top"},
            "is_locked": {"type": "BOOLEAN", "description": "Whether the topic is locked for new replies"},
            "view_count": {"type": "INTEGER", "description": "Number of views"},
            "last_post_id": {"type": "UUID", "description": "ID of the last post in the topic", "foreign_key": "forum_posts.post_id"},
            "last_post_at": {"type": "TIMESTAMP", "description": "When the last post was made"},
            "created_at": {"type": "TIMESTAMP", "description": "When the topic was created"},
            "updated_at": {"type": "TIMESTAMP", "description": "When the topic was last updated"}
        },
        "indexes": [
            {"columns": ["slug"], "unique": True},
            {"columns": ["category_id"]},
            {"columns": ["user_id"]},
            {"columns": ["status"]},
            {"columns": ["created_at"]},
            {"columns": ["last_post_at"]}  # For sorting by activity
        ]
    }
    
    forum_posts = {
        "table_name": "forum_posts",
        "primary_key": "post_id",
        "columns": {
            "post_id": {"type": "UUID", "description": "Unique identifier for the post"},
            "topic_id": {"type": "UUID", "description": "Foreign key to forum_topics table", "foreign_key": "forum_topics.topic_id"},
            "user_id": {"type": "UUID", "description": "Foreign key to users table", "foreign_key": "users.user_id"},
            "content": {"type": "TEXT", "description": "Post content"},
            "content_html": {"type": "TEXT", "description": "Rendered HTML version of content"},
            "status": {"type": "VARCHAR(20)", "description": "Post status (published, deleted, etc.)"},
            "is_first_post": {"type": "BOOLEAN", "description": "Whether this is the first post in the topic"},
            "is_best_answer": {"type": "BOOLEAN", "description": "Whether this post was marked as the best answer"},
            "edited_at": {"type": "TIMESTAMP", "description": "When the post was last edited"},
            "edited_by": {"type": "UUID", "description": "Who edited the post", "foreign_key": "users.user_id"},
            "created_at": {"type": "TIMESTAMP", "description": "When the post was created"},
            "updated_at": {"type": "TIMESTAMP", "description": "When the post was last updated"}
        },
        "indexes": [
            {"columns": ["topic_id"]},
            {"columns": ["user_id"]},
            {"columns": ["created_at"]},
            {"columns": ["topic_id", "created_at"]},  # For paginated topic view
            {"columns": ["topic_id", "is_best_answer"]}  # For finding answers quickly
        ]
    }
    
    post_reactions = {
        "table_name": "post_reactions",
        "primary_key": ["post_id", "user_id", "reaction_type"],
        "columns": {
            "post_id": {"type": "UUID", "description": "Foreign key to forum_posts table", "foreign_key": "forum_posts.post_id"},
            "user_id": {"type": "UUID", "description": "Foreign key to users table", "foreign_key": "users.user_id"},
            "reaction_type": {"type": "VARCHAR(20)", "description": "Type of reaction (like, disagree, etc.)"},
            "created_at": {"type": "TIMESTAMP", "description": "When the reaction was created"}
        },
        "indexes": [
            {"columns": ["post_id", "user_id", "reaction_type"], "unique": True},
            {"columns": ["post_id"]},
            {"columns": ["user_id"]}
        ]
    }
    
    # Trading setup sharing tables
    trading_setups = {
        "table_name": "trading_setups",
        "primary_key": "setup_id",
        "columns": {
            "setup_id": {"type": "UUID", "description": "Unique identifier for the setup"},
            "user_id": {"type": "UUID", "description": "Foreign key to users table", "foreign_key": "users.user_id"},
            "title": {"type": "VARCHAR(255)", "description": "Setup title"},
            "description": {"type": "TEXT", "description": "Setup description"},
            "symbol": {"type": "VARCHAR(20)", "description": "Trading symbol"},
            "timeframes": {"type": "VARCHAR(255)", "description": "Comma-separated list of timeframes"},
            "strategy_parameters": {"type": "JSONB", "description": "JSON object containing strategy parameters"},
            "risk_parameters": {"type": "JSONB", "description": "JSON object containing risk parameters"},
            "chart_image_url": {"type": "VARCHAR(255)", "description": "URL to chart image"},
            "status": {"type": "VARCHAR(20)", "description": "Setup status (published, draft, etc.)"},
            "visibility": {"type": "VARCHAR(20)", "description": "Setup visibility (public, private, followers)"},
            "performance_metrics": {"type": "JSONB", "description": "JSON object containing performance metrics"},
            "tags": {"type": "VARCHAR(255)", "description": "Comma-separated list of tags"},
            "created_at": {"type": "TIMESTAMP", "description": "When the setup was created"},
            "updated_at": {"type": "TIMESTAMP", "description": "When the setup was last updated"}
        },
        "indexes": [
            {"columns": ["user_id"]},
            {"columns": ["symbol"]},
            {"columns": ["status"]},
            {"columns": ["created_at"]},
            {"columns": ["tags"], "type": "GIN"}  # For tag searching
        ]
    }
    
    setup_comments = {
        "table_name": "setup_comments",
        "primary_key": "comment_id",
        "columns": {
            "comment_id": {"type": "UUID", "description": "Unique identifier for the comment"},
            "setup_id": {"type": "UUID", "description": "Foreign key to trading_setups table", "foreign_key": "trading_setups.setup_id"},
            "user_id": {"type": "UUID", "description": "Foreign key to users table", "foreign_key": "users.user_id"},
            "content": {"type": "TEXT", "description": "Comment content"},
            "status": {"type": "VARCHAR(20)", "description": "Comment status (published, deleted, etc.)"},
            "created_at": {"type": "TIMESTAMP", "description": "When the comment was created"},
            "updated_at": {"type": "TIMESTAMP", "description": "When the comment was last updated"}
        },
        "indexes": [
            {"columns": ["setup_id"]},
            {"columns": ["user_id"]},
            {"columns": ["created_at"]}
        ]
    }
    
    setup_likes = {
        "table_name": "setup_likes",
        "primary_key": ["setup_id", "user_id"],
        "columns": {
            "setup_id": {"type": "UUID", "description": "Foreign key to trading_setups table", "foreign_key": "trading_setups.setup_id"},
            "user_id": {"type": "UUID", "description": "Foreign key to users table", "foreign_key": "users.user_id"},
            "created_at": {"type": "TIMESTAMP", "description": "When the like was created"}
        },
        "indexes": [
            {"columns": ["setup_id"]},
            {"columns": ["user_id"]}
        ]
    }
    
    # Trading signals tables
    trading_signals = {
        "table_name": "trading_signals",
        "primary_key": "signal_id",
        "columns": {
            "signal_id": {"type": "UUID", "description": "Unique identifier for the signal"},
            "user_id": {"type": "UUID", "description": "Foreign key to users table", "foreign_key": "users.user_id"},
            "setup_id": {"type": "UUID", "description": "Optional foreign key to trading_setups table", "foreign_key": "trading_setups.setup_id"},
            "title": {"type": "VARCHAR(255)", "description": "Signal title"},
            "description": {"type": "TEXT", "description": "Signal description"},
            "symbol": {"type": "VARCHAR(20)", "description": "Trading symbol"},
            "timeframe": {"type": "VARCHAR(20)", "description": "Primary timeframe for the signal"},
            "direction": {"type": "VARCHAR(10)", "description": "Trade direction (long, short)"},
            "entry_price": {"type": "DECIMAL(20,8)", "description": "Entry price"},
            "stop_loss": {"type": "DECIMAL(20,8)", "description": "Stop loss price"},
            "take_profit_levels": {"type": "JSONB", "description": "JSON array of take profit levels"},
            "risk_reward_ratio": {"type": "DECIMAL(10,2)", "description": "Risk-to-reward ratio"},
            "chart_image_url": {"type": "VARCHAR(255)", "description": "URL to chart image"},
            "status": {"type": "VARCHAR(20)", "description": "Signal status (active, triggered, completed, etc.)"},
            "visibility": {"type": "VARCHAR(20)", "description": "Signal visibility (public, private, subscribers)"},
            "expiry_time": {"type": "TIMESTAMP", "description": "When the signal expires"},
            "created_at": {"type": "TIMESTAMP", "description": "When the signal was created"},
            "updated_at": {"type": "TIMESTAMP", "description": "When the signal was last updated"},
            "triggered_at": {"type": "TIMESTAMP", "description": "When the signal was triggered"},
            "completed_at": {"type": "TIMESTAMP", "description": "When the signal was completed"},
            "result": {"type": "VARCHAR(20)", "description": "Signal result (win, loss, partial, etc.)"},
            "profit_loss": {"type": "DECIMAL(10,2)", "description": "Profit/loss percentage"},
            "notes": {"type": "TEXT", "description": "Additional notes or updates"}
        },
        "indexes": [
            {"columns": ["user_id"]},
            {"columns": ["setup_id"]},
            {"columns": ["symbol"]},
            {"columns": ["status"]},
            {"columns": ["created_at"]},
            {"columns": ["triggered_at"]},
            {"columns": ["completed_at"]}
        ]
    }
    
    signal_subscriptions = {
        "table_name": "signal_subscriptions",
        "primary_key": ["user_id", "provider_id"],
        "columns": {
            "user_id": {"type": "UUID", "description": "Subscriber's user ID", "foreign_key": "users.user_id"},
            "provider_id": {"type": "UUID", "description": "Signal provider's user ID", "foreign_key": "users.user_id"},
            "subscription_level": {"type": "VARCHAR(20)", "description": "Subscription level (free, premium, etc.)"},
            "notifications_enabled": {"type": "BOOLEAN", "description": "Whether notifications are enabled"},
            "created_at": {"type": "TIMESTAMP", "description": "When the subscription was created"},
            "expires_at": {"type": "TIMESTAMP", "description": "When the subscription expires (null for unlimited)"},
            "last_notification_at": {"type": "TIMESTAMP", "description": "When the last notification was sent"}
        },
        "indexes": [
            {"columns": ["user_id"]},
            {"columns": ["provider_id"]}
        ]
    }
    
    # Performance leaderboard tables
    performance_metrics = {
        "table_name": "performance_metrics",
        "primary_key": ["user_id", "timeframe", "period"],
        "columns": {
            "user_id": {"type": "UUID", "description": "Foreign key to users table", "foreign_key": "users.user_id"},
            "timeframe": {"type": "VARCHAR(20)", "description": "Timeframe (daily, weekly, monthly, all-time)"},
            "period": {"type": "VARCHAR(20)", "description": "Period (current, previous, specific date range)"},
            "win_rate": {"type": "DECIMAL(5,2)", "description": "Win rate percentage"},
            "profit_factor": {"type": "DECIMAL(10,2)", "description": "Profit factor"},
            "sharpe_ratio": {"type": "DECIMAL(10,2)", "description": "Sharpe ratio"},
            "max_drawdown": {"type": "DECIMAL(10,2)", "description": "Maximum drawdown percentage"},
            "total_trades": {"type": "INTEGER", "description": "Total number of trades"},
            "avg_trade": {"type": "DECIMAL(10,2)", "description": "Average trade percentage"},
            "best_trade": {"type": "DECIMAL(10,2)", "description": "Best trade percentage"},
            "worst_trade": {"type": "DECIMAL(10,2)", "description": "Worst trade percentage"},
            "detailed_metrics": {"type": "JSONB", "description": "Additional detailed metrics as JSON"},
            "updated_at": {"type": "TIMESTAMP", "description": "When metrics were last updated"}
        },
        "indexes": [
            {"columns": ["user_id", "timeframe", "period"], "unique": True},
            {"columns": ["timeframe", "period", "win_rate"]},
            {"columns": ["timeframe", "period", "profit_factor"]},
            {"columns": ["timeframe", "period", "sharpe_ratio"]}
        ]
    }
    
    # Notification and activity tables
    notifications = {
        "table_name": "notifications",
        "primary_key": "notification_id",
        "columns": {
            "notification_id": {"type": "UUID", "description": "Unique identifier for the notification"},
            "user_id": {"type": "UUID", "description": "Target user ID", "foreign_key": "users.user_id"},
            "type": {"type": "VARCHAR(50)", "description": "Notification type"},
            "content": {"type": "TEXT", "description": "Notification content"},
            "metadata": {"type": "JSONB", "description": "Additional data as JSON"},
            "link": {"type": "VARCHAR(255)", "description": "Optional link to follow"},
            "is_read": {"type": "BOOLEAN", "description": "Whether the notification has been read"},
            "created_at": {"type": "TIMESTAMP", "description": "When the notification was created"}
        },
        "indexes": [
            {"columns": ["user_id"]},
            {"columns": ["user_id", "created_at"]},  # For efficient feed loading
            {"columns": ["user_id", "is_read"]}  # For unread counts
        ]
    }
    
    user_activity = {
        "table_name": "user_activity",
        "primary_key": "activity_id",
        "columns": {
            "activity_id": {"type": "UUID", "description": "Unique identifier for the activity"},
            "user_id": {"type": "UUID", "description": "User ID", "foreign_key": "users.user_id"},
            "activity_type": {"type": "VARCHAR(50)", "description": "Type of activity"},
            "content_type": {"type": "VARCHAR(50)", "description": "Type of content (post, setup, signal, etc.)"},
            "content_id": {"type": "UUID", "description": "ID of the content"},
            "metadata": {"type": "JSONB", "description": "Additional data as JSON"},
            "created_at": {"type": "TIMESTAMP", "description": "When the activity occurred"}
        },
        "indexes": [
            {"columns": ["user_id", "created_at"]},  # For activity feed
            {"columns": ["content_type", "content_id"]},  # For finding activity related to content
            {"columns": ["created_at"]}  # For global activity feed
        ]
    }
    
    # Common query patterns and optimizations
    common_queries = {
        "user_feed": {
            "description": "Get personalized feed for a user",
            "query": """
                SELECT * FROM (
                    -- Recent forum posts in followed categories
                    SELECT fp.post_id as content_id, 'forum_post' as content_type, fp.created_at
                    FROM forum_posts fp
                    JOIN forum_topics ft ON fp.topic_id = ft.topic_id
                    JOIN forum_categories fc ON ft.category_id = fc.category_id
                    JOIN category_subscriptions cs ON cs.category_id = fc.category_id
                    WHERE cs.user_id = :user_id AND fp.status = 'published'
                    
                    UNION ALL
                    
                    -- Recent trading setups from followed users
                    SELECT ts.setup_id as content_id, 'trading_setup' as content_type, ts.created_at
                    FROM trading_setups ts
                    JOIN user_follows uf ON ts.user_id = uf.followed_id
                    WHERE uf.follower_id = :user_id AND ts.status = 'published' AND ts.visibility = 'public'
                    
                    UNION ALL
                    
                    -- Recent signals from subscribed providers
                    SELECT sg.signal_id as content_id, 'trading_signal' as content_type, sg.created_at
                    FROM trading_signals sg
                    JOIN signal_subscriptions ss ON sg.user_id = ss.provider_id
                    WHERE ss.user_id = :user_id AND sg.status = 'active'
                ) AS combined
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """,
            "indexes_used": [
                "forum_posts(status, created_at)",
                "forum_topics(category_id)",
                "category_subscriptions(user_id, category_id)",
                "trading_setups(status, visibility, created_at)",
                "user_follows(follower_id, followed_id)",
                "trading_signals(status, created_at)",
                "signal_subscriptions(user_id, provider_id)"
            ]
        },
        
        "leaderboard": {
            "description": "Get performance leaderboard",
            "query": """
                SELECT u.user_id, u.username, u.profile_picture_url, 
                       pm.win_rate, pm.profit_factor, pm.total_trades, pm.avg_trade
                FROM performance_metrics pm
                JOIN users u ON pm.user_id = u.user_id
                WHERE pm.timeframe = :timeframe AND pm.period = :period
                ORDER BY pm.profit_factor DESC
                LIMIT :limit OFFSET :offset
            """,
            "indexes_used": [
                "performance_metrics(timeframe, period, profit_factor)"
            ]
        },
        
        "topic_with_posts": {
            "description": "Get a forum topic with paginated posts",
            "query": """
                -- Get topic details
                SELECT * FROM forum_topics WHERE topic_id = :topic_id;
                
                -- Get paginated posts
                SELECT fp.*, u.username, u.profile_picture_url, 
                       (SELECT COUNT(*) FROM post_reactions pr WHERE pr.post_id = fp.post_id AND pr.reaction_type = 'like') as like_count
                FROM forum_posts fp
                JOIN users u ON fp.user_id = u.user_id
                WHERE fp.topic_id = :topic_id AND fp.status = 'published'
                ORDER BY fp.created_at
                LIMIT :limit OFFSET :offset
            """,
            "indexes_used": [
                "forum_topics(topic_id)",
                "forum_posts(topic_id, status, created_at)",
                "post_reactions(post_id, reaction_type)"
            ]
        },
        
        "user_notifications": {
            "description": "Get unread notifications for a user",
            "query": """
                SELECT * FROM notifications 
                WHERE user_id = :user_id AND is_read = false
                ORDER BY created_at DESC
                LIMIT :limit
            """,
            "indexes_used": [
                "notifications(user_id, is_read, created_at)"
            ]
        }
    }
    
    # Denormalized data design for high performance
    denormalized_tables = {
        "forum_topics_with_stats": {
            "description": "Denormalized view of forum topics with statistics for fast listing",
            "columns": [
                "All columns from forum_topics",
                "category_name", "category_slug",
                "author_username", "author_profile_picture_url",
                "post_count", "like_count",
                "last_post_author_username",
                "last_post_created_at"
            ]
        },
        
        "trading_setups_with_stats": {
            "description": "Denormalized view of trading setups with statistics for fast listing",
            "columns": [
                "All columns from trading_setups",
                "author_username", "author_profile_picture_url",
                "comment_count", "like_count",
                "performance_summary"
            ]
        }
    }
    
    # Partition strategies for large tables
    partitioning_strategy = {
        "forum_posts": {
            "strategy": "RANGE",
            "column": "created_at",
            "interval": "1 MONTH",
            "description": "Partition forum posts by month for better performance on large forums"
        },
        
        "trading_signals": {
            "strategy": "LIST",
            "column": "status",
            "partitions": ["active", "triggered", "completed", "expired"],
            "description": "Partition trading signals by status for efficient querying of active signals"
        },
        
        "user_activity": {
            "strategy": "RANGE",
            "column": "created_at",
            "interval": "1 MONTH",
            "description": "Partition user activity by month to maintain performance as activity grows"
        }
    }
    
    # Indexing strategies for high-volume tables
    indexing_strategies = {
        "partial_indexes": [
            {
                "table": "forum_posts",
                "columns": ["topic_id", "created_at"],
                "condition": "status = 'published'",
                "description": "Partial index for published posts only"
            },
            {
                "table": "trading_signals",
                "columns": ["user_id", "created_at"],
                "condition": "status = 'active'",
                "description": "Partial index for active signals only"
            }
        ],
        
        "expression_indexes": [
            {
                "table": "trading_setups",
                "expression": "LOWER(title)",
                "description": "Case-insensitive search on setup title"
            },
            {
                "table": "forum_topics",
                "expression": "to_tsvector('english', title || ' ' || first_post_content)",
                "description": "Full-text search on topic title and first post"
            }
        ]
    }
    
    # Sharding strategy for future horizontal scaling
    sharding_strategy = {
        "user_data": {
            "shard_key": "user_id",
            "algorithm": "consistent hashing",
            "tables": ["users", "user_profiles", "user_activity", "notifications"],
            "description": "Shard user-related data by user_id to distribute load"
        },
        
        "content_data": {
            "shard_key": "created_at",
            "algorithm": "range-based",
            "tables": ["forum_posts", "trading_signals", "trading_setups"],
            "description": "Shard content by creation date for historical vs. recent content optimization"
        }
    }


# Utility functions for creating SQL

def generate_create_table_sql(table_def: Dict) -> str:
    """
    Generate SQL CREATE TABLE statement from table definition.
    
    Args:
        table_def: Table definition dictionary
        
    Returns:
        SQL CREATE TABLE statement
    """
    table_name = table_def["table_name"]
    columns = table_def["columns"]
    primary_key = table_def.get("primary_key", "")
    
    # Build column definitions
    column_defs = []
    for col_name, col_info in columns.items():
        col_type = col_info["type"]
        constraints = []
        
        if "foreign_key" in col_info:
            constraints.append(f"REFERENCES {col_info['foreign_key']}")
            
        if col_name == primary_key or (isinstance(primary_key, list) and col_name in primary_key):
            if not isinstance(primary_key, list) or len(primary_key) == 1:
                constraints.append("PRIMARY KEY")
                
        column_def = f"{col_name} {col_type}"
        if constraints:
            column_def += " " + " ".join(constraints)
            
        column_defs.append(column_def)
    
    # Add composite primary key if needed
    if isinstance(primary_key, list) and len(primary_key) > 1:
        column_defs.append(f"PRIMARY KEY ({', '.join(primary_key)})")
    
    # Build index definitions
    index_defs = []
    for idx in table_def.get("indexes", []):
        idx_cols = idx["columns"]
        idx_unique = idx.get("unique", False)
        idx_type = idx.get("type", "")
        
        idx_name = f"idx_{table_name}_{'_'.join(idx_cols)}"
        unique_str = "UNIQUE " if idx_unique else ""
        type_str = f"USING {idx_type} " if idx_type else ""
        
        index_def = f"CREATE {unique_str}INDEX {idx_name} ON {table_name} {type_str}({', '.join(idx_cols)});"
        index_defs.append(index_def)
    
    # Combine everything
    create_table = f"CREATE TABLE {table_name} (\n    " + \
                   ",\n    ".join(column_defs) + \
                   "\n);"
    
    return create_table + "\n" + "\n".join(index_defs)


def get_table_dependencies() -> Dict[str, List[str]]:
    """
    Get dependencies between tables for proper creation order.
    
    Returns:
        Dictionary mapping table names to their dependencies
    """
    schema = Schema()
    dependencies = {}
    
    for attr_name in dir(schema):
        if attr_name.startswith("_") or not isinstance(getattr(schema, attr_name), dict):
            continue
            
        table_def = getattr(schema, attr_name)
        if "table_name" not in table_def:
            continue
            
        table_name = table_def["table_name"]
        table_deps = []
        
        # Find dependencies through foreign keys
        for col_info in table_def["columns"].values():
            if "foreign_key" in col_info:
                fk_parts = col_info["foreign_key"].split(".")
                if len(fk_parts) >= 1:
                    dep_table = fk_parts[0]
                    if dep_table != table_name:  # Avoid self-references
                        table_deps.append(dep_table)
        
        dependencies[table_name] = table_deps
    
    return dependencies


def topological_sort(dependencies: Dict[str, List[str]]) -> List[str]:
    """
    Sort tables by dependency order.
    
    Args:
        dependencies: Dictionary mapping table names to their dependencies
        
    Returns:
        List of table names in proper creation order
    """
    result = []
    visited = set()
    temp_visited = set()
    
    def visit(node):
        if node in temp_visited:
            raise ValueError(f"Circular dependency detected involving {node}")
        if node in visited:
            return
            
        temp_visited.add(node)
        
        for dep in dependencies.get(node, []):
            visit(dep)
            
        temp_visited.remove(node)
        visited.add(node)
        result.append(node)
    
    for node in dependencies:
        if node not in visited:
            visit(node)
            
    return result


def generate_schema_sql() -> str:
    """
    Generate complete SQL schema for all tables.
    
    Returns:
        SQL statements to create the entire schema
    """
    schema = Schema()
    dependencies = get_table_dependencies()
    sorted_tables = topological_sort(dependencies)
    
    sql_statements = []
    
    for table_name in sorted_tables:
        # Find the table definition
        table_def = None
        for attr_name in dir(schema):
            if attr_name.startswith("_") or not isinstance(getattr(schema, attr_name), dict):
                continue
                
            attr_val = getattr(schema, attr_name)
            if "table_name" in attr_val and attr_val["table_name"] == table_name:
                table_def = attr_val
                break
        
        if table_def:
            sql_statements.append(generate_create_table_sql(table_def))
    
    return "\n\n".join(sql_statements) 