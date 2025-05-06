"""
Content moderation system for MT 9 EMA Backtester community features.

This module provides automated and manual moderation capabilities to ensure
community content adheres to guidelines and maintains quality.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Union, Any
from datetime import datetime
import json
from enum import Enum
import hashlib

from mtfema_backtester.community.feature_flags import FeatureFlags

logger = logging.getLogger(__name__)

class ContentType(Enum):
    """Types of content that can be moderated."""
    FORUM_POST = "forum_post"
    FORUM_COMMENT = "forum_comment"  
    SIGNAL = "signal"
    SETUP = "setup"
    USER_PROFILE = "user_profile"
    PRIVATE_MESSAGE = "private_message"

class ModerationType(Enum):
    """Types of moderation actions."""
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"  # Requires manual review
    AUTO_FLAGGED = "auto_flagged"  # Flagged by automated system
    USER_REPORTED = "user_reported"  # Reported by users

class ModeratorRole(Enum):
    """Roles for moderators."""
    ADMIN = "admin"  # Full access to all moderation features
    MODERATOR = "moderator"  # Can moderate most content
    COMMUNITY_MODERATOR = "community_moderator"  # Trusted community members with limited moderation powers
    AUTO = "auto"  # Automated moderation system

class ContentModerator:
    """
    Content moderation system that combines automated and manual moderation.
    
    Features:
    - Automated content filtering based on rules and ML models
    - Manual moderation queue for human review
    - Reporting system for community-based moderation
    - Audit logging of all moderation actions
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern for global moderation access."""
        if cls._instance is None:
            cls._instance = super(ContentModerator, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the content moderation system.
        
        Args:
            config_path: Path to moderation configuration file
        """
        # Skip re-initialization if already initialized
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        self.config_path = config_path
        
        # Load feature flags
        self.feature_flags = FeatureFlags()
        
        # Default configuration
        self.config = {
            "auto_moderation_enabled": True,
            "community_reporting_enabled": True,
            "manual_review_threshold": 0.7,  # Confidence threshold for requiring manual review
            "rejection_threshold": 0.9,  # Confidence threshold for automatic rejection
            "max_reports_before_review": 3,  # Number of user reports before content is flagged for review
            "forbidden_patterns": [
                r'\b(password|credit\s*card|ssn|social\s*security)\b',  # Sensitive information
                r'\b(http|https|www)\S+\.(ru|cn|io|xyz)\b',  # Suspicious URLs
                r'\b(buy|sell|invest|sign\s*up).{0,20}(now|today|cryptocurrency|forex|stock)\b',  # Spam patterns
            ],
            "forbidden_words": [
                # Placeholder - actual list would be more comprehensive and properly managed
                "spam", "scam", "hack", "cheat", "illegal", "password"
            ],
            "moderation_queue_limit": 100,  # Maximum items in the moderation queue
        }
        
        # Override with configuration file if provided
        if config_path:
            try:
                with open(config_path, 'r') as f:
                    file_config = json.load(f)
                    self.config.update(file_config)
                logger.info(f"Loaded moderation configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading moderation config from {config_path}: {e}")
        
        # Compile regex patterns for performance
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) 
                                  for pattern in self.config["forbidden_patterns"]]
        
        # Create a set of forbidden words for faster lookup
        self.forbidden_words_set = set(word.lower() for word in self.config["forbidden_words"])
        
        # Initialize moderation queue
        self.moderation_queue = []
        
        # Initialize moderation history
        self.moderation_history = []
        
        logger.info("Content moderation system initialized")
    
    def moderate_content(self, 
                         content: str,
                         metadata: Dict[str, Any],
                         content_type: ContentType,
                         user_id: str,
                         auto_approve: bool = False) -> Tuple[bool, str, float]:
        """
        Moderate content using automated rules and ML model.
        
        Args:
            content: The text content to moderate
            metadata: Additional metadata about the content
            content_type: Type of content being moderated
            user_id: ID of the user who created the content
            auto_approve: Whether to automatically approve content from trusted users
            
        Returns:
            Tuple of (is_approved, moderation_reason, confidence_score)
        """
        # Check if content moderation is enabled
        if not self.feature_flags.flags.get("content_moderation", True):
            return True, "Content moderation disabled", 1.0
        
        # Auto-approve for trusted users if enabled
        if auto_approve and self._is_trusted_user(user_id):
            self._log_moderation_action(
                content_id=self._generate_content_id(content, metadata),
                content_type=content_type,
                user_id=user_id,
                action=ModerationType.APPROVED,
                reason="Trusted user auto-approval",
                moderator_id="system",
                moderator_role=ModeratorRole.AUTO
            )
            return True, "Trusted user auto-approval", 1.0
        
        # Apply rule-based filtering
        is_approved, reason, confidence = self._apply_moderation_rules(content, metadata)
        
        # If confidence is below thresholds, queue for manual review
        if (is_approved and confidence < self.config["manual_review_threshold"]) or \
           (not is_approved and confidence < self.config["rejection_threshold"]):
            self._add_to_moderation_queue(content, metadata, content_type, user_id, reason, confidence)
            return False, "Queued for manual review", confidence
        
        # Log the moderation action
        action = ModerationType.APPROVED if is_approved else ModerationType.REJECTED
        self._log_moderation_action(
            content_id=self._generate_content_id(content, metadata),
            content_type=content_type,
            user_id=user_id,
            action=action,
            reason=reason,
            moderator_id="system",
            moderator_role=ModeratorRole.AUTO
        )
        
        return is_approved, reason, confidence
    
    def report_content(self, 
                      content_id: str,
                      content_type: ContentType,
                      reporter_id: str,
                      reason: str) -> bool:
        """
        Allow users to report inappropriate content.
        
        Args:
            content_id: ID of the content being reported
            content_type: Type of content being reported
            reporter_id: ID of the user making the report
            reason: Reason for reporting
            
        Returns:
            Whether the content was flagged for review
        """
        # Check if community reporting is enabled
        if not self.config["community_reporting_enabled"]:
            logger.warning("Community reporting attempted but feature is disabled")
            return False
        
        # Count existing reports for this content
        existing_reports = sum(1 for item in self.moderation_history 
                              if item["content_id"] == content_id and 
                              item["action"] == ModerationType.USER_REPORTED.value)
        
        # Add the report to moderation history
        self._log_moderation_action(
            content_id=content_id,
            content_type=content_type,
            user_id=reporter_id,
            action=ModerationType.USER_REPORTED,
            reason=reason,
            moderator_id=reporter_id,
            moderator_role=ModeratorRole.AUTO
        )
        
        # Check if threshold is reached to flag for review
        if existing_reports + 1 >= self.config["max_reports_before_review"]:
            # Flag the content for review
            self._log_moderation_action(
                content_id=content_id,
                content_type=content_type,
                user_id="",  # No specific user
                action=ModerationType.FLAGGED,
                reason=f"Received {existing_reports + 1} user reports",
                moderator_id="system",
                moderator_role=ModeratorRole.AUTO
            )
            return True
            
        return False
    
    def manual_moderate(self,
                       content_id: str,
                       action: ModerationType,
                       moderator_id: str,
                       moderator_role: ModeratorRole,
                       reason: str = "") -> bool:
        """
        Apply manual moderation to content.
        
        Args:
            content_id: ID of the content to moderate
            action: Moderation action to take
            moderator_id: ID of the moderator
            moderator_role: Role of the moderator
            reason: Reason for the moderation action
            
        Returns:
            Whether the moderation action was applied successfully
        """
        # Find the item in the moderation queue
        queue_item = next((item for item in self.moderation_queue 
                          if item["content_id"] == content_id), None)
                          
        # Log the moderation action
        self._log_moderation_action(
            content_id=content_id,
            content_type=queue_item["content_type"] if queue_item else None,
            user_id=queue_item["user_id"] if queue_item else "",
            action=action,
            reason=reason,
            moderator_id=moderator_id,
            moderator_role=moderator_role
        )
        
        # Remove from queue if present
        if queue_item:
            self.moderation_queue.remove(queue_item)
            return True
            
        return False
    
    def get_moderation_queue(self, 
                           moderator_role: ModeratorRole,
                           content_types: Optional[List[ContentType]] = None,
                           limit: int = 20,
                           offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get items from the moderation queue.
        
        Args:
            moderator_role: Role of the moderator viewing the queue
            content_types: Filter by content types
            limit: Maximum number of items to return
            offset: Offset for pagination
            
        Returns:
            List of moderation queue items
        """
        # Filter by content types if specified
        filtered_queue = self.moderation_queue
        if content_types:
            content_type_values = [ct.value for ct in content_types]
            filtered_queue = [item for item in self.moderation_queue 
                             if item["content_type"] in content_type_values]
        
        # Apply pagination
        paginated_queue = filtered_queue[offset:offset + limit]
        
        return paginated_queue
    
    def get_moderation_history(self,
                             content_id: Optional[str] = None,
                             user_id: Optional[str] = None,
                             moderator_id: Optional[str] = None,
                             action: Optional[ModerationType] = None,
                             limit: int = 20,
                             offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get moderation history with optional filtering.
        
        Args:
            content_id: Filter by specific content
            user_id: Filter by content creator
            moderator_id: Filter by moderator
            action: Filter by moderation action
            limit: Maximum number of items to return
            offset: Offset for pagination
            
        Returns:
            List of moderation history items
        """
        # Apply filters
        filtered_history = self.moderation_history
        
        if content_id:
            filtered_history = [item for item in filtered_history 
                               if item["content_id"] == content_id]
        
        if user_id:
            filtered_history = [item for item in filtered_history 
                               if item["user_id"] == user_id]
        
        if moderator_id:
            filtered_history = [item for item in filtered_history 
                               if item["moderator_id"] == moderator_id]
        
        if action:
            filtered_history = [item for item in filtered_history 
                               if item["action"] == action.value]
        
        # Sort by timestamp (newest first)
        sorted_history = sorted(filtered_history, 
                               key=lambda x: x["timestamp"], 
                               reverse=True)
        
        # Apply pagination
        paginated_history = sorted_history[offset:offset + limit]
        
        return paginated_history
    
    def _apply_moderation_rules(self, 
                              content: str, 
                              metadata: Dict[str, Any]) -> Tuple[bool, str, float]:
        """
        Apply rule-based moderation to content.
        
        Args:
            content: The content to moderate
            metadata: Additional metadata about the content
            
        Returns:
            Tuple of (is_approved, reason, confidence)
        """
        # Check for empty content
        if not content or content.strip() == "":
            return False, "Empty content", 1.0
        
        # Check content length
        if len(content) < 3:
            return False, "Content too short", 1.0
        
        # Check for forbidden words
        content_lower = content.lower()
        for word in self.forbidden_words_set:
            if word in content_lower:
                return False, f"Forbidden word: {word}", 0.95
        
        # Check for forbidden patterns
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(content):
                return False, f"Matched forbidden pattern #{i+1}", 0.9
        
        # Additional checks based on content type can be added here
        content_type = metadata.get("content_type", "")
        
        if content_type == ContentType.FORUM_POST.value:
            # Forum-specific checks (e.g., title quality)
            title = metadata.get("title", "")
            if title and len(title) < 5:
                return False, "Forum post title too short", 0.85
        
        elif content_type == ContentType.SIGNAL.value:
            # Signal-specific checks
            if "symbol" not in metadata or not metadata["symbol"]:
                return False, "Signal missing required symbol", 0.95
        
        # All checks passed
        return True, "Content approved", 0.85
    
    def _add_to_moderation_queue(self,
                                content: str,
                                metadata: Dict[str, Any],
                                content_type: ContentType,
                                user_id: str,
                                reason: str,
                                confidence: float):
        """
        Add an item to the moderation queue.
        
        Args:
            content: The content to moderate
            metadata: Additional metadata about the content
            content_type: Type of content being moderated
            user_id: ID of the user who created the content
            reason: Reason for moderation
            confidence: Confidence score of the automated decision
        """
        # Check if queue is full
        if len(self.moderation_queue) >= self.config["moderation_queue_limit"]:
            # Remove oldest item if queue is full
            self.moderation_queue.pop(0)
        
        # Generate a content ID for tracking
        content_id = self._generate_content_id(content, metadata)
        
        # Create queue item
        queue_item = {
            "content_id": content_id,
            "content": content,
            "metadata": metadata,
            "content_type": content_type.value,
            "user_id": user_id,
            "reason": reason,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "status": ModerationType.FLAGGED.value
        }
        
        # Add to queue
        self.moderation_queue.append(queue_item)
        
        # Log the queuing action
        self._log_moderation_action(
            content_id=content_id,
            content_type=content_type,
            user_id=user_id,
            action=ModerationType.FLAGGED,
            reason=reason,
            moderator_id="system",
            moderator_role=ModeratorRole.AUTO
        )
        
        logger.info(f"Content {content_id} added to moderation queue: {reason}")
    
    def _log_moderation_action(self,
                              content_id: str,
                              content_type: ContentType,
                              user_id: str,
                              action: ModerationType,
                              reason: str,
                              moderator_id: str,
                              moderator_role: ModeratorRole):
        """
        Log a moderation action for audit purposes.
        
        Args:
            content_id: ID of the moderated content
            content_type: Type of the content
            user_id: ID of the user who created the content
            action: Moderation action taken
            reason: Reason for the action
            moderator_id: ID of the moderator
            moderator_role: Role of the moderator
        """
        log_entry = {
            "content_id": content_id,
            "content_type": content_type.value,
            "user_id": user_id,
            "action": action.value,
            "reason": reason,
            "moderator_id": moderator_id,
            "moderator_role": moderator_role.value,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to history
        self.moderation_history.append(log_entry)
        
        # Log to system logs
        logger.info(f"Moderation action: {action.value} on {content_type.value} by {moderator_role.value}")
    
    def _generate_content_id(self, content: str, metadata: Dict[str, Any]) -> str:
        """
        Generate a unique ID for content based on its content and metadata.
        
        Args:
            content: The content text
            metadata: Additional metadata
            
        Returns:
            Unique content ID
        """
        # Create a string representation of the metadata
        metadata_str = json.dumps(metadata, sort_keys=True)
        
        # Combine content and metadata
        combined = f"{content}|{metadata_str}"
        
        # Generate hash
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def _is_trusted_user(self, user_id: str) -> bool:
        """
        Check if a user is trusted for auto-approval.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Whether the user is trusted
        """
        # This would typically check a database of trusted users
        # For now, it's a stub implementation
        return False

# Helper functions for easier access
def moderate_content(content: str, 
                    metadata: Dict[str, Any],
                    content_type: ContentType,
                    user_id: str,
                    auto_approve: bool = False) -> Tuple[bool, str, float]:
    """
    Moderate content using the global moderator instance.
    
    Args:
        content: The text content to moderate
        metadata: Additional metadata about the content
        content_type: Type of content being moderated
        user_id: ID of the user who created the content
        auto_approve: Whether to automatically approve content from trusted users
        
    Returns:
        Tuple of (is_approved, moderation_reason, confidence_score)
    """
    moderator = ContentModerator()
    return moderator.moderate_content(content, metadata, content_type, user_id, auto_approve)

def report_content(content_id: str,
                  content_type: ContentType,
                  reporter_id: str,
                  reason: str) -> bool:
    """
    Report content for moderation review.
    
    Args:
        content_id: ID of the content being reported
        content_type: Type of content being reported
        reporter_id: ID of the user making the report
        reason: Reason for reporting
        
    Returns:
        Whether the content was flagged for review
    """
    moderator = ContentModerator()
    return moderator.report_content(content_id, content_type, reporter_id, reason)
