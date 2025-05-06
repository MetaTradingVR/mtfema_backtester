"""
Feature Flagging System for the MT 9 EMA Backtester.

This module provides a feature flagging system that allows for gradual rollout
of features, A/B testing, and controlling access to experimental features.
"""

import os
import json
from enum import Enum
from typing import Dict, Any, Optional, List, Set, Callable
import logging
import random
from pathlib import Path

# Setup logger
logger = logging.getLogger(__name__)

class FeatureState(Enum):
    """Possible states for a feature flag."""
    OFF = "off"         # Feature is disabled for everyone
    ON = "on"           # Feature is enabled for everyone
    GRADUAL = "gradual" # Feature is being gradually rolled out by percentage
    BETA = "beta"       # Feature is only available to beta users
    ADMIN = "admin"     # Feature is only available to admins
    TARGETED = "targeted" # Feature is only available to specific users

class FeatureFlag:
    """Represents a single feature flag with its metadata and state."""
    
    def __init__(
        self,
        name: str,
        description: str,
        default_state: FeatureState,
        rollout_percentage: float = 100.0,
        target_users: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        dependencies: Optional[List[str]] = None
    ):
        """
        Initialize a feature flag.
        
        Args:
            name: Unique identifier for the feature
            description: Human-readable description
            default_state: Default state for the feature
            rollout_percentage: For GRADUAL state, percentage of users who get the feature
            target_users: For TARGETED state, list of user IDs who get the feature
            tags: Optional tags for categorizing/filtering features
            dependencies: Optional list of features this feature depends on
        """
        self.name = name
        self.description = description
        self.default_state = default_state
        self.rollout_percentage = max(0, min(100, rollout_percentage))
        self.target_users = set(target_users or [])
        self.tags = set(tags or [])
        self.dependencies = set(dependencies or [])
        self.override_state: Optional[FeatureState] = None
        self.environment_override: Optional[FeatureState] = None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert feature flag to dictionary representation."""
        return {
            "name": self.name,
            "description": self.description,
            "default_state": self.default_state.value,
            "rollout_percentage": self.rollout_percentage,
            "target_users": list(self.target_users),
            "tags": list(self.tags),
            "dependencies": list(self.dependencies),
            "override_state": self.override_state.value if self.override_state else None,
            "environment_override": self.environment_override.value if self.environment_override else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureFlag':
        """Create a feature flag from dictionary representation."""
        flag = cls(
            name=data["name"],
            description=data["description"],
            default_state=FeatureState(data["default_state"]),
            rollout_percentage=data.get("rollout_percentage", 100.0),
            target_users=data.get("target_users", []),
            tags=data.get("tags", []),
            dependencies=data.get("dependencies", [])
        )
        
        if data.get("override_state"):
            flag.override_state = FeatureState(data["override_state"])
            
        if data.get("environment_override"):
            flag.environment_override = FeatureState(data["environment_override"])
            
        return flag


class FeatureFlagManager:
    """Manages feature flags for the application."""
    
    # Singleton instance
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(FeatureFlagManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the feature flag manager.
        
        Args:
            config_file: Path to feature flags configuration file
        """
        # Only initialize once (singleton pattern)
        if self._initialized:
            return
            
        self._initialized = True
        self._config_file = config_file or "features.json"
        self._flags: Dict[str, FeatureFlag] = {}
        
        # User roles cache for faster lookup
        self._admin_users: Set[str] = set()
        self._beta_users: Set[str] = set()
        
        # Load feature flags
        self._load_feature_flags()
        
        # Environment variable prefix for overrides
        self._env_prefix = "MTFEMA_FEATURE_"
        
        # Apply environment overrides
        self._apply_environment_overrides()
    
    def _load_feature_flags(self) -> None:
        """Load feature flags from configuration file."""
        config_path = Path(self._config_file)
        
        # Use default flags if config file doesn't exist
        if not config_path.exists():
            logger.info(f"Feature flags config file not found: {self._config_file}. Using default flags.")
            self._initialize_default_flags()
            return
        
        try:
            with open(config_path, 'r') as f:
                config_data = json.load(f)
                
            # Load feature flags
            for flag_data in config_data.get("features", []):
                flag = FeatureFlag.from_dict(flag_data)
                self._flags[flag.name] = flag
                
            # Load user roles
            self._admin_users = set(config_data.get("admin_users", []))
            self._beta_users = set(config_data.get("beta_users", []))
                
            logger.info(f"Loaded {len(self._flags)} feature flags from {self._config_file}")
        except Exception as e:
            logger.error(f"Error loading feature flags: {str(e)}")
            self._initialize_default_flags()
    
    def _initialize_default_flags(self) -> None:
        """Initialize default feature flags."""
        # Community features - initially gradual rollout
        self.register_feature(
            FeatureFlag(
                name="community.forums",
                description="Community discussion forums",
                default_state=FeatureState.GRADUAL,
                rollout_percentage=25.0,
                tags=["community", "core"]
            )
        )
        
        self.register_feature(
            FeatureFlag(
                name="community.signals",
                description="Trading signals system",
                default_state=FeatureState.BETA,
                tags=["community", "trading"]
            )
        )
        
        self.register_feature(
            FeatureFlag(
                name="community.sharing",
                description="Trading setup sharing",
                default_state=FeatureState.BETA,
                tags=["community", "trading"]
            )
        )
        
        self.register_feature(
            FeatureFlag(
                name="community.profiles",
                description="Enhanced user profiles",
                default_state=FeatureState.GRADUAL,
                rollout_percentage=50.0,
                tags=["community", "core"]
            )
        )
        
        # Security features - on by default
        self.register_feature(
            FeatureFlag(
                name="security.2fa",
                description="Two-factor authentication",
                default_state=FeatureState.ON,
                tags=["security", "core"]
            )
        )
        
        # Performance features - on by default
        self.register_feature(
            FeatureFlag(
                name="performance.metrics_collection",
                description="Anonymous usage metrics collection",
                default_state=FeatureState.ON,
                tags=["performance", "analytics"]
            )
        )
        
        # Experimental features - admin only
        self.register_feature(
            FeatureFlag(
                name="experimental.ai_signals",
                description="AI-generated trading signals",
                default_state=FeatureState.ADMIN,
                tags=["experimental", "trading"]
            )
        )
    
    def _apply_environment_overrides(self) -> None:
        """Apply feature flag overrides from environment variables."""
        for env_var, env_value in os.environ.items():
            if not env_var.startswith(self._env_prefix):
                continue
                
            # Extract feature name from environment variable
            feature_name = env_var[len(self._env_prefix):].lower().replace('_', '.')
            
            if feature_name not in self._flags:
                logger.warning(f"Unknown feature flag in environment variable: {feature_name}")
                continue
                
            # Parse state value
            try:
                state = FeatureState(env_value.lower())
                self._flags[feature_name].environment_override = state
                logger.info(f"Applied environment override for {feature_name}: {state.value}")
            except ValueError:
                logger.warning(f"Invalid feature state in environment variable {env_var}: {env_value}")
    
    def register_feature(self, feature: FeatureFlag) -> None:
        """
        Register a new feature flag.
        
        Args:
            feature: Feature flag to register
        """
        self._flags[feature.name] = feature
        logger.debug(f"Registered feature flag: {feature.name}")
    
    def is_enabled(self, feature_name: str, user_id: Optional[str] = None) -> bool:
        """
        Check if a feature is enabled for a specific user.
        
        Args:
            feature_name: Name of the feature to check
            user_id: Optional user ID to check for
            
        Returns:
            True if the feature is enabled, False otherwise
        """
        # Handle unknown features
        if feature_name not in self._flags:
            logger.warning(f"Unknown feature flag: {feature_name}")
            return False
            
        feature = self._flags[feature_name]
        
        # Check dependencies first
        for dependency in feature.dependencies:
            if not self.is_enabled(dependency, user_id):
                logger.debug(f"Feature {feature_name} disabled due to dependency: {dependency}")
                return False
        
        # Determine effective state, with overrides taking precedence
        state = feature.default_state
        if feature.environment_override is not None:
            state = feature.environment_override
        elif feature.override_state is not None:
            state = feature.override_state
        
        # Check state
        if state == FeatureState.ON:
            return True
        elif state == FeatureState.OFF:
            return False
        elif state == FeatureState.ADMIN:
            return user_id in self._admin_users
        elif state == FeatureState.BETA:
            return user_id in self._beta_users
        elif state == FeatureState.TARGETED:
            return user_id in feature.target_users
        elif state == FeatureState.GRADUAL:
            # For gradual rollout, use deterministic hashing based on user ID
            # so the same user always gets the same experience
            if user_id is None:
                return False
                
            # Create a hash of feature name + user ID
            hash_input = f"{feature_name}:{user_id}"
            hash_value = hash(hash_input) % 100
            
            # Check if the hash falls within the rollout percentage
            return hash_value < feature.rollout_percentage
        
        # Default to disabled
        return False
    
    def set_override(self, feature_name: str, state: FeatureState) -> bool:
        """
        Set an override state for a feature flag.
        
        Args:
            feature_name: Name of the feature to override
            state: New state for the feature
            
        Returns:
            True if successful, False otherwise
        """
        if feature_name not in self._flags:
            logger.warning(f"Cannot override unknown feature flag: {feature_name}")
            return False
            
        self._flags[feature_name].override_state = state
        logger.info(f"Set override for feature {feature_name}: {state.value}")
        return True
    
    def reset_override(self, feature_name: str) -> bool:
        """
        Reset a feature flag override to use the default state.
        
        Args:
            feature_name: Name of the feature to reset
            
        Returns:
            True if successful, False otherwise
        """
        if feature_name not in self._flags:
            logger.warning(f"Cannot reset unknown feature flag: {feature_name}")
            return False
            
        self._flags[feature_name].override_state = None
        logger.info(f"Reset override for feature {feature_name}")
        return True
    
    def get_feature(self, feature_name: str) -> Optional[FeatureFlag]:
        """
        Get a feature flag by name.
        
        Args:
            feature_name: Name of the feature to get
            
        Returns:
            FeatureFlag object or None if not found
        """
        return self._flags.get(feature_name)
    
    def list_features(self, 
                     tag: Optional[str] = None, 
                     state: Optional[FeatureState] = None) -> List[FeatureFlag]:
        """
        List all feature flags, optionally filtered by tag or state.
        
        Args:
            tag: Optional tag to filter by
            state: Optional state to filter by
            
        Returns:
            List of matching feature flags
        """
        result = list(self._flags.values())
        
        if tag:
            result = [flag for flag in result if tag in flag.tags]
            
        if state:
            result = [flag for flag in result if flag.default_state == state]
            
        return result
    
    def save_to_file(self, file_path: Optional[str] = None) -> bool:
        """
        Save current feature flags configuration to file.
        
        Args:
            file_path: Optional path to save to (uses default if not specified)
            
        Returns:
            True if successful, False otherwise
        """
        file_path = file_path or self._config_file
        
        try:
            config_data = {
                "features": [flag.to_dict() for flag in self._flags.values()],
                "admin_users": list(self._admin_users),
                "beta_users": list(self._beta_users)
            }
            
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            logger.info(f"Saved {len(self._flags)} feature flags to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving feature flags: {str(e)}")
            return False
    
    def update_user_roles(self, 
                        admin_users: Optional[List[str]] = None,
                        beta_users: Optional[List[str]] = None) -> None:
        """
        Update user role assignments.
        
        Args:
            admin_users: List of admin user IDs
            beta_users: List of beta user IDs
        """
        if admin_users is not None:
            self._admin_users = set(admin_users)
            
        if beta_users is not None:
            self._beta_users = set(beta_users)
    
    def add_user_to_role(self, user_id: str, role: str) -> bool:
        """
        Add a user to a role.
        
        Args:
            user_id: User ID to add
            role: Role to add user to ('admin' or 'beta')
            
        Returns:
            True if successful, False otherwise
        """
        if role == 'admin':
            self._admin_users.add(user_id)
            return True
        elif role == 'beta':
            self._beta_users.add(user_id)
            return True
        else:
            logger.warning(f"Unknown role: {role}")
            return False
    
    def remove_user_from_role(self, user_id: str, role: str) -> bool:
        """
        Remove a user from a role.
        
        Args:
            user_id: User ID to remove
            role: Role to remove user from ('admin' or 'beta')
            
        Returns:
            True if successful, False otherwise
        """
        if role == 'admin' and user_id in self._admin_users:
            self._admin_users.remove(user_id)
            return True
        elif role == 'beta' and user_id in self._beta_users:
            self._beta_users.remove(user_id)
            return True
        else:
            return False


# Global instance
feature_flags = FeatureFlagManager()

def get_feature_flags() -> FeatureFlagManager:
    """
    Get the global feature flags manager instance.
    
    Returns:
        FeatureFlagManager instance
    """
    return feature_flags

def is_feature_enabled(feature_name: str, user_id: Optional[str] = None) -> bool:
    """
    Check if a feature is enabled for a specific user.
    
    Args:
        feature_name: Name of the feature to check
        user_id: Optional user ID to check for
        
    Returns:
        True if the feature is enabled, False otherwise
    """
    return feature_flags.is_enabled(feature_name, user_id)

def with_feature(feature_name: str):
    """
    Decorator to conditionally execute a function based on a feature flag.
    
    Args:
        feature_name: Name of the feature to check
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Extract user_id from kwargs, with None as default
            user_id = kwargs.get('user_id')
            
            # Check if feature is enabled
            if feature_flags.is_enabled(feature_name, user_id):
                return func(*args, **kwargs)
            else:
                logger.debug(f"Function {func.__name__} skipped due to disabled feature: {feature_name}")
                return None
        return wrapper
    return decorator 