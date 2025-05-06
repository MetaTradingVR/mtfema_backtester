"""
Reputation System for MT 9 EMA Backtester community.

This module provides a comprehensive reputation system for tracking user contributions,
awarding points, managing badges, and generating leaderboards.
"""

import os
import json
import logging
import uuid
import threading
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Setup logger
logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Types of community actions that award reputation points."""
    FORUM_POST_CREATE = "forum_post_create"
    FORUM_POST_LIKE = "forum_post_like"
    FORUM_POST_LIKED = "forum_post_liked"
    FORUM_SOLUTION = "forum_solution"
    
    SIGNAL_CREATE = "signal_create"
    SIGNAL_SUCCESS = "signal_success"
    SIGNAL_FOLLOWED = "signal_followed"
    
    SETUP_SHARE = "setup_share"
    SETUP_LIKED = "setup_liked"
    
    BACKTEST_SHARE = "backtest_share"
    
    DAILY_LOGIN = "daily_login"
    PROFILE_COMPLETE = "profile_complete"


@dataclass
class Badge:
    """Represents a badge that can be earned by users."""
    id: str
    name: str
    description: str
    icon: str
    points_required: int
    action_type: Optional[str] = None
    action_count: Optional[int] = None
    is_special: bool = False


class ReputationSystem:
    """
    Reputation system for the MT 9 EMA Backtester community.
    
    Features:
    - Track user reputation points
    - Award badges for accomplishments
    - Generate leaderboards
    - Track user activity and contributions
    """
    
    # Singleton instance
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern for global access."""
        if cls._instance is None:
            cls._instance = super(ReputationSystem, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, storage_path: Optional[str] = None):
        """
        Initialize the reputation system.
        
        Args:
            storage_path: Directory for storing reputation data
        """
        # Skip re-initialization if already initialized
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        
        # Set storage path
        self._storage_path = storage_path or os.path.join(
            os.path.expanduser("~"),
            ".mtfema",
            "community",
            "reputation"
        )
        
        # Ensure storage directory exists
        os.makedirs(self._storage_path, exist_ok=True)
        
        # Initialize data structures
        self._users: Dict[str, Dict[str, Any]] = {}
        self._badges: Dict[str, Badge] = {}
        self._action_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Thread lock for thread safety
        self._lock = threading.RLock()
        
        # Load data
        self._load_data()
        
        # Initialize system with default badges
        self._initialize_badges()
        
        logger.info("Reputation system initialized")
    
    def _load_data(self) -> None:
        """Load reputation data from storage."""
        # Load user reputation data
        user_file = os.path.join(self._storage_path, "user_reputation.json")
        if os.path.exists(user_file):
            try:
                with open(user_file, 'r') as f:
                    self._users = json.load(f)
                logger.info(f"Loaded reputation data for {len(self._users)} users")
            except Exception as e:
                logger.error(f"Error loading user reputation data: {str(e)}")
        
        # Load action history
        history_file = os.path.join(self._storage_path, "action_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    self._action_history = json.load(f)
                logger.info(f"Loaded action history for {len(self._action_history)} users")
            except Exception as e:
                logger.error(f"Error loading action history: {str(e)}")
    
    def _save_data(self) -> None:
        """Save reputation data to storage."""
        with self._lock:
            # Save user reputation data
            user_file = os.path.join(self._storage_path, "user_reputation.json")
            try:
                with open(user_file, 'w') as f:
                    json.dump(self._users, f, indent=2)
            except Exception as e:
                logger.error(f"Error saving user reputation data: {str(e)}")
            
            # Save action history
            history_file = os.path.join(self._storage_path, "action_history.json")
            try:
                with open(history_file, 'w') as f:
                    json.dump(self._action_history, f, indent=2)
            except Exception as e:
                logger.error(f"Error saving action history: {str(e)}")
    
    def _initialize_badges(self) -> None:
        """Initialize the system with default badges."""
        # Forum badges
        self._badges["forum_novice"] = Badge(
            id="forum_novice",
            name="Forum Novice",
            description="Created your first forum post",
            icon="📝",
            points_required=10,
            action_type=ActionType.FORUM_POST_CREATE.value,
            action_count=1
        )
        
        self._badges["forum_contributor"] = Badge(
            id="forum_contributor",
            name="Forum Contributor",
            description="Created 10 forum posts",
            icon="✍️",
            points_required=100,
            action_type=ActionType.FORUM_POST_CREATE.value,
            action_count=10
        )
        
        self._badges["forum_expert"] = Badge(
            id="forum_expert",
            name="Forum Expert",
            description="Created 50 forum posts",
            icon="🖋️",
            points_required=500,
            action_type=ActionType.FORUM_POST_CREATE.value,
            action_count=50
        )
        
        self._badges["helpful_advisor"] = Badge(
            id="helpful_advisor",
            name="Helpful Advisor",
            description="Your post was marked as a solution 5 times",
            icon="💡",
            points_required=250,
            action_type=ActionType.FORUM_SOLUTION.value,
            action_count=5
        )
        
        # Signal badges
        self._badges["signal_provider"] = Badge(
            id="signal_provider",
            name="Signal Provider",
            description="Shared your first trading signal",
            icon="📊",
            points_required=20,
            action_type=ActionType.SIGNAL_CREATE.value,
            action_count=1
        )
        
        self._badges["signal_master"] = Badge(
            id="signal_master",
            name="Signal Master",
            description="Shared 20 successful trading signals",
            icon="📈",
            points_required=400,
            action_type=ActionType.SIGNAL_SUCCESS.value,
            action_count=20
        )
        
        self._badges["popular_trader"] = Badge(
            id="popular_trader",
            name="Popular Trader",
            description="Your signals were followed 50 times",
            icon="👥",
            points_required=300,
            action_type=ActionType.SIGNAL_FOLLOWED.value,
            action_count=50
        )
        
        # Setup badges
        self._badges["setup_sharer"] = Badge(
            id="setup_sharer",
            name="Setup Sharer",
            description="Shared your first trading setup",
            icon="📋",
            points_required=15,
            action_type=ActionType.SETUP_SHARE.value,
            action_count=1
        )
        
        self._badges["setup_guru"] = Badge(
            id="setup_guru",
            name="Setup Guru",
            description="Your setups received 100 likes",
            icon="👍",
            points_required=350,
            action_type=ActionType.SETUP_LIKED.value,
            action_count=100
        )
        
        # Reputation level badges
        self._badges["bronze_trader"] = Badge(
            id="bronze_trader",
            name="Bronze Trader",
            description="Reached 100 reputation points",
            icon="🥉",
            points_required=100,
            is_special=True
        )
        
        self._badges["silver_trader"] = Badge(
            id="silver_trader",
            name="Silver Trader",
            description="Reached 500 reputation points",
            icon="🥈",
            points_required=500,
            is_special=True
        )
        
        self._badges["gold_trader"] = Badge(
            id="gold_trader",
            name="Gold Trader",
            description="Reached 1000 reputation points",
            icon="🥇",
            points_required=1000,
            is_special=True
        )
        
        self._badges["diamond_trader"] = Badge(
            id="diamond_trader",
            name="Diamond Trader",
            description="Reached 5000 reputation points",
            icon="💎",
            points_required=5000,
            is_special=True
        )
        
        logger.info(f"Initialized {len(self._badges)} badges")
    
    def award_points(self, user_id: str, action_type: str, context: Optional[Dict[str, Any]] = None) -> int:
        """
        Award reputation points to a user for an action.
        
        Args:
            user_id: ID of the user
            action_type: Type of action performed
            context: Additional context about the action
            
        Returns:
            Number of points awarded
        """
        if not user_id:
            logger.warning("Cannot award points: no user ID provided")
            return 0
            
        with self._lock:
            # Initialize user data if not exists
            if user_id not in self._users:
                self._users[user_id] = {
                    "user_id": user_id,
                    "points": 0,
                    "level": 1,
                    "badges": [],
                    "actions": {}
                }
            
            # Initialize action history if not exists
            if user_id not in self._action_history:
                self._action_history[user_id] = []
            
            # Determine points to award based on action type
            points = self._get_points_for_action(action_type)
            
            # Update user's points
            self._users[user_id]["points"] += points
            
            # Update action count
            if action_type not in self._users[user_id]["actions"]:
                self._users[user_id]["actions"][action_type] = 0
            self._users[user_id]["actions"][action_type] += 1
            
            # Record action in history
            action_record = {
                "action_id": str(uuid.uuid4()),
                "user_id": user_id,
                "action_type": action_type,
                "points": points,
                "timestamp": datetime.now().isoformat(),
                "context": context or {}
            }
            self._action_history[user_id].append(action_record)
            
            # Check for new badges
            self._check_and_award_badges(user_id)
            
            # Update user level
            self._update_user_level(user_id)
            
            # Save data
            self._save_data()
            
            logger.info(f"Awarded {points} points to user {user_id} for {action_type}")
            return points
    
    def _get_points_for_action(self, action_type: str) -> int:
        """
        Get the number of points for an action type.
        
        Args:
            action_type: Type of action
            
        Returns:
            Number of points
        """
        # Points awarded for different actions
        points_map = {
            ActionType.FORUM_POST_CREATE.value: 10,
            ActionType.FORUM_POST_LIKE.value: 1,
            ActionType.FORUM_POST_LIKED.value: 5,
            ActionType.FORUM_SOLUTION.value: 25,
            
            ActionType.SIGNAL_CREATE.value: 15,
            ActionType.SIGNAL_SUCCESS.value: 20,
            ActionType.SIGNAL_FOLLOWED.value: 5,
            
            ActionType.SETUP_SHARE.value: 15,
            ActionType.SETUP_LIKED.value: 5,
            
            ActionType.BACKTEST_SHARE.value: 10,
            
            ActionType.DAILY_LOGIN.value: 2,
            ActionType.PROFILE_COMPLETE.value: 5
        }
        
        return points_map.get(action_type, 0)
    
    def _check_and_award_badges(self, user_id: str) -> None:
        """
        Check if user has earned any new badges and award them.
        
        Args:
            user_id: ID of the user
        """
        user_data = self._users[user_id]
        user_points = user_data["points"]
        user_actions = user_data["actions"]
        user_badges = user_data["badges"]
        
        # Check each badge
        for badge_id, badge in self._badges.items():
            # Skip if user already has this badge
            if badge_id in user_badges:
                continue
                
            # Check if user meets requirements
            if badge.is_special:
                # Special badges are based on total points
                if user_points >= badge.points_required:
                    user_badges.append(badge_id)
                    logger.info(f"Awarded badge {badge.name} to user {user_id}")
            elif badge.action_type:
                # Action-based badges require a certain number of actions
                action_count = user_actions.get(badge.action_type, 0)
                if action_count >= badge.action_count:
                    user_badges.append(badge_id)
                    logger.info(f"Awarded badge {badge.name} to user {user_id}")
    
    def _update_user_level(self, user_id: str) -> None:
        """
        Update a user's level based on points.
        
        Args:
            user_id: ID of the user
        """
        user_data = self._users[user_id]
        user_points = user_data["points"]
        
        # Define point thresholds for each level
        level_thresholds = [
            0,      # Level 1: 0+ points
            100,    # Level 2: 100+ points
            300,    # Level 3: 300+ points
            600,    # Level 4: 600+ points
            1000,   # Level 5: 1000+ points
            1500,   # Level 6: 1500+ points
            2100,   # Level 7: 2100+ points
            3000,   # Level 8: 3000+ points
            4000,   # Level 9: 4000+ points
            5500,   # Level 10: 5500+ points
            7500,   # Level 11: 7500+ points
            10000   # Level 12: 10000+ points
        ]
        
        # Determine current level
        current_level = 1
        for i, threshold in enumerate(level_thresholds):
            if user_points >= threshold:
                current_level = i + 1
        
        # Update user level if changed
        if current_level != user_data["level"]:
            user_data["level"] = current_level
            logger.info(f"User {user_id} reached level {current_level}")
    
    def get_user_reputation(self, user_id: str) -> Dict[str, Any]:
        """
        Get reputation data for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            User reputation data including points, level, and badges
        """
        with self._lock:
            # Return default data if user not found
            if user_id not in self._users:
                return {
                    "user_id": user_id,
                    "points": 0,
                    "level": 1,
                    "badges": [],
                    "rank": None,
                    "next_level_points": 100
                }
            
            user_data = self._users[user_id]
            
            # Calculate next level points
            level_thresholds = [0, 100, 300, 600, 1000, 1500, 2100, 3000, 4000, 5500, 7500, 10000]
            current_level = user_data["level"]
            
            next_level_points = level_thresholds[current_level] if current_level < len(level_thresholds) else None
            
            # Calculate user's rank
            rank = self._calculate_user_rank(user_id)
            
            # Return reputation data
            return {
                "user_id": user_id,
                "points": user_data["points"],
                "level": user_data["level"],
                "badges": user_data["badges"],
                "rank": rank,
                "next_level_points": next_level_points
            }
    
    def _calculate_user_rank(self, user_id: str) -> Optional[int]:
        """
        Calculate a user's rank based on points.
        
        Args:
            user_id: ID of the user
            
        Returns:
            User's rank or None if not ranked
        """
        # Get all users sorted by points
        users_by_points = sorted(
            self._users.values(),
            key=lambda u: u["points"],
            reverse=True
        )
        
        # Find user's position
        for i, user in enumerate(users_by_points):
            if user["user_id"] == user_id:
                return i + 1
                
        return None
    
    def get_user_badges(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get badges earned by a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of badge objects
        """
        with self._lock:
            # Return empty list if user not found
            if user_id not in self._users:
                return []
            
            user_data = self._users[user_id]
            badge_ids = user_data["badges"]
            
            # Convert badge IDs to badge objects
            badges = []
            for badge_id in badge_ids:
                if badge_id in self._badges:
                    badge = self._badges[badge_id]
                    badges.append({
                        "id": badge.id,
                        "name": badge.name,
                        "description": badge.description,
                        "icon": badge.icon,
                        "is_special": badge.is_special
                    })
            
            return badges
    
    def generate_leaderboard(self, category: str = "reputation", 
                           timeframe: str = "all_time",
                           limit: int = 10) -> List[Dict[str, Any]]:
        """
        Generate a leaderboard of users.
        
        Args:
            category: What to rank by ('reputation', 'signals', 'forum', etc.)
            timeframe: Time period ('day', 'week', 'month', 'all_time')
            limit: Maximum number of users to include
            
        Returns:
            List of user data sorted by rank
        """
        with self._lock:
            # Handle different categories
            if category == "reputation":
                # Sort by total reputation points
                sorted_users = sorted(
                    self._users.values(),
                    key=lambda u: u["points"],
                    reverse=True
                )
            elif category == "signals":
                # Sort by signal creation and success
                sorted_users = sorted(
                    self._users.values(),
                    key=lambda u: (
                        u["actions"].get(ActionType.SIGNAL_SUCCESS.value, 0) * 2 +
                        u["actions"].get(ActionType.SIGNAL_CREATE.value, 0)
                    ),
                    reverse=True
                )
            elif category == "forum":
                # Sort by forum activity
                sorted_users = sorted(
                    self._users.values(),
                    key=lambda u: (
                        u["actions"].get(ActionType.FORUM_POST_CREATE.value, 0) +
                        u["actions"].get(ActionType.FORUM_SOLUTION.value, 0) * 3
                    ),
                    reverse=True
                )
            else:
                # Default to reputation
                sorted_users = sorted(
                    self._users.values(),
                    key=lambda u: u["points"],
                    reverse=True
                )
            
            # Limit number of results
            leaderboard = sorted_users[:limit]
            
            # Add rank and convert to return format
            result = []
            for i, user in enumerate(leaderboard):
                # Build leaderboard entry
                entry = {
                    "rank": i + 1,
                    "user_id": user["user_id"],
                    "points": user["points"],
                    "level": user["level"]
                }
                
                # Add category-specific stats
                if category == "signals":
                    entry["signal_count"] = user["actions"].get(ActionType.SIGNAL_CREATE.value, 0)
                    entry["successful_signals"] = user["actions"].get(ActionType.SIGNAL_SUCCESS.value, 0)
                elif category == "forum":
                    entry["post_count"] = user["actions"].get(ActionType.FORUM_POST_CREATE.value, 0)
                    entry["solutions"] = user["actions"].get(ActionType.FORUM_SOLUTION.value, 0)
                
                result.append(entry)
            
            return result
    
    def get_action_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent action history for a user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of actions to retrieve
            
        Returns:
            List of recent actions
        """
        with self._lock:
            # Return empty list if user not found
            if user_id not in self._action_history:
                return []
            
            # Get actions and sort by timestamp (newest first)
            actions = self._action_history[user_id]
            sorted_actions = sorted(
                actions,
                key=lambda a: a["timestamp"],
                reverse=True
            )
            
            # Limit number of results
            return sorted_actions[:limit]
    
    def reset_user_reputation(self, user_id: str) -> bool:
        """
        Reset a user's reputation (for moderation purposes).
        
        Args:
            user_id: ID of the user
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            # Check if user exists
            if user_id not in self._users:
                return False
            
            # Reset user data
            self._users[user_id] = {
                "user_id": user_id,
                "points": 0,
                "level": 1,
                "badges": [],
                "actions": {}
            }
            
            # Clear action history
            self._action_history[user_id] = []
            
            # Save data
            self._save_data()
            
            logger.info(f"Reset reputation for user {user_id}")
            return True


def get_reputation_system() -> ReputationSystem:
    """
    Get the global reputation system instance.
    
    Returns:
        ReputationSystem instance
    """
    return ReputationSystem()

def award_points(user_id: str, action_type: str, context: Optional[Dict[str, Any]] = None) -> int:
    """
    Award reputation points to a user for an action.
    
    Args:
        user_id: ID of the user
        action_type: Type of action performed
        context: Additional context about the action
        
    Returns:
        Number of points awarded
    """
    system = get_reputation_system()
    return system.award_points(user_id, action_type, context)

def get_user_reputation(user_id: str) -> Dict[str, Any]:
    """
    Get reputation data for a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        User reputation data including points, level, and badges
    """
    system = get_reputation_system()
    return system.get_user_reputation(user_id)

def get_user_badges(user_id: str) -> List[Dict[str, Any]]:
    """
    Get badges earned by a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of badge objects
    """
    system = get_reputation_system()
    return system.get_user_badges(user_id)

def generate_leaderboard(category: str = "reputation", 
                        timeframe: str = "all_time",
                        limit: int = 10) -> List[Dict[str, Any]]:
    """
    Generate a leaderboard of users.
    
    Args:
        category: What to rank by ('reputation', 'signals', 'forum', etc.)
        timeframe: Time period ('day', 'week', 'month', 'all_time')
        limit: Maximum number of users to include
        
    Returns:
        List of user data sorted by rank
    """
    system = get_reputation_system()
    return system.generate_leaderboard(category, timeframe, limit)
