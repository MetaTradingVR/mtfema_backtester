"""
Security Framework for MT 9 EMA Backtester.

This module provides security functionalities for authentication, authorization,
data protection, and privacy controls in the MT 9 EMA Backtester application.
"""

import os
import json
import time
import uuid
import base64
import hashlib
import logging
import threading
import secrets
import re
from enum import Enum
from typing import Dict, Any, Optional, List, Set, Callable, Tuple, Union
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False

# Setup logger
logger = logging.getLogger(__name__)

class UserRole(Enum):
    """User roles for role-based access control."""
    GUEST = "guest"         # Unauthenticated or limited access
    USER = "user"           # Standard authenticated user
    PREMIUM = "premium"     # Premium user with additional features
    MODERATOR = "moderator" # Community moderator
    ADMIN = "admin"         # Administrator with full access


class PermissionLevel(Enum):
    """Permission levels for different operations."""
    READ = "read"             # Read-only access
    WRITE = "write"           # Write access (create, update)
    DELETE = "delete"         # Delete access
    MODERATE = "moderate"     # Moderation access (approve, reject)
    ADMIN = "admin"           # Administrative access


@dataclass
class User:
    """Represents a user in the system."""
    
    # Unique identifier
    id: str
    
    # Username (for display and login)
    username: str
    
    # Email address
    email: str
    
    # Password hash (never store actual passwords)
    password_hash: str
    
    # Salt for password hashing
    salt: str
    
    # User roles
    roles: List[UserRole] = field(default_factory=lambda: [UserRole.USER])
    
    # Last login timestamp
    last_login: Optional[float] = None
    
    # Account creation timestamp
    created_at: float = field(default_factory=time.time)
    
    # Whether two-factor authentication is enabled
    two_factor_enabled: bool = False
    
    # Secret key for two-factor authentication
    two_factor_secret: Optional[str] = None
    
    # Whether the account is active
    is_active: bool = True
    
    # Whether the email has been verified
    email_verified: bool = False
    
    # Additional user data
    meta: Dict[str, Any] = field(default_factory=dict)
    
    def has_role(self, role: UserRole) -> bool:
        """
        Check if the user has a specific role.
        
        Args:
            role: Role to check
            
        Returns:
            True if the user has the role, False otherwise
        """
        return role in self.roles
    
    def has_permission(self, resource: str, level: PermissionLevel) -> bool:
        """
        Check if the user has a specific permission level for a resource.
        
        Args:
            resource: Resource to check permissions for
            level: Permission level to check
            
        Returns:
            True if the user has the permission, False otherwise
        """
        # Admins have all permissions
        if UserRole.ADMIN in self.roles:
            return True
            
        # Moderators have moderate, write, and read permissions
        if level == PermissionLevel.MODERATE and UserRole.MODERATOR in self.roles:
            return True
            
        # Premium users have additional permissions for certain resources
        if UserRole.PREMIUM in self.roles:
            # Premium-only features
            if resource.startswith("premium."):
                return level != PermissionLevel.ADMIN
        
        # Standard users have basic read/write permissions
        if level == PermissionLevel.READ:
            return True
            
        if level == PermissionLevel.WRITE and UserRole.USER in self.roles:
            # Users can write to their own resources
            if resource.startswith(f"user.{self.id}."):
                return True
            
            # Users can write to public resources like forum posts
            if resource.startswith("public."):
                return True
                
        # By default, no permission
        return False


class SecurityManager:
    """Manages security aspects of the application."""
    
    # Singleton instance
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(SecurityManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, data_dir: Optional[str] = None, jwt_secret: Optional[str] = None):
        """
        Initialize the security manager.
        
        Args:
            data_dir: Directory for storing security data
            jwt_secret: Secret key for JWT token signing
        """
        # Only initialize once (singleton pattern)
        if self._initialized:
            return
            
        self._initialized = True
        
        # Set data directory
        self._data_dir = data_dir or os.path.join(
            os.path.expanduser("~"),
            ".mtfema",
            "security"
        )
        
        # Ensure data directory exists
        os.makedirs(self._data_dir, exist_ok=True)
        
        # Initialize users storage
        self._users: Dict[str, User] = {}
        self._username_to_id: Dict[str, str] = {}
        self._email_to_id: Dict[str, str] = {}
        
        # Initialize session storage
        self._sessions: Dict[str, Dict[str, Any]] = {}
        
        # Initialize lock for thread safety
        self._lock = threading.RLock()
        
        # Setup JWT
        self._jwt_secret = jwt_secret or self._load_or_create_jwt_secret()
        
        # Setup encryption
        self._encryption_key = self._load_or_create_encryption_key()
        
        # Load users
        self._load_users()
        
        # Password policy
        self._password_min_length = 8
        self._password_requires_uppercase = True
        self._password_requires_lowercase = True
        self._password_requires_digit = True
        self._password_requires_special = True
        
        logger.info("Security manager initialized")
    
    def _load_or_create_jwt_secret(self) -> str:
        """
        Load the JWT secret key or create a new one.
        
        Returns:
            JWT secret key
        """
        secret_file = os.path.join(self._data_dir, "jwt_secret.key")
        
        if os.path.exists(secret_file):
            try:
                with open(secret_file, 'r') as f:
                    return f.read().strip()
            except Exception as e:
                logger.error(f"Error loading JWT secret: {str(e)}")
        
        # Generate a new secret
        new_secret = secrets.token_hex(32)
        
        try:
            with open(secret_file, 'w') as f:
                f.write(new_secret)
                
            logger.info("Generated new JWT secret")
        except Exception as e:
            logger.error(f"Error saving JWT secret: {str(e)}")
            
        return new_secret
    
    def _load_or_create_encryption_key(self) -> Optional[bytes]:
        """
        Load the encryption key or create a new one.
        
        Returns:
            Encryption key as bytes or None if encryption is not available
        """
        if not ENCRYPTION_AVAILABLE:
            logger.warning("Encryption not available. Install cryptography package for data encryption.")
            return None
            
        key_file = os.path.join(self._data_dir, "encryption.key")
        
        if os.path.exists(key_file):
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error loading encryption key: {str(e)}")
        
        # Generate a new key
        new_key = Fernet.generate_key()
        
        try:
            with open(key_file, 'wb') as f:
                f.write(new_key)
                
            logger.info("Generated new encryption key")
        except Exception as e:
            logger.error(f"Error saving encryption key: {str(e)}")
            
        return new_key
    
    def _load_users(self) -> None:
        """Load users from storage."""
        users_file = os.path.join(self._data_dir, "users.json")
        
        if not os.path.exists(users_file):
            logger.info("No users file found, starting with empty users database")
            return
            
        try:
            with open(users_file, 'r') as f:
                user_data = json.load(f)
                
            for user_dict in user_data:
                # Convert roles from strings to UserRole enum
                roles = [UserRole(role) for role in user_dict.get("roles", ["user"])]
                
                user = User(
                    id=user_dict["id"],
                    username=user_dict["username"],
                    email=user_dict["email"],
                    password_hash=user_dict["password_hash"],
                    salt=user_dict["salt"],
                    roles=roles,
                    last_login=user_dict.get("last_login"),
                    created_at=user_dict.get("created_at", time.time()),
                    two_factor_enabled=user_dict.get("two_factor_enabled", False),
                    two_factor_secret=user_dict.get("two_factor_secret"),
                    is_active=user_dict.get("is_active", True),
                    email_verified=user_dict.get("email_verified", False),
                    meta=user_dict.get("meta", {})
                )
                
                self._users[user.id] = user
                self._username_to_id[user.username.lower()] = user.id
                self._email_to_id[user.email.lower()] = user.id
                
            logger.info(f"Loaded {len(self._users)} users from storage")
        except Exception as e:
            logger.error(f"Error loading users: {str(e)}")
    
    def _save_users(self) -> None:
        """Save users to storage."""
        users_file = os.path.join(self._data_dir, "users.json")
        
        try:
            user_data = []
            
            for user in self._users.values():
                user_dict = {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "password_hash": user.password_hash,
                    "salt": user.salt,
                    "roles": [role.value for role in user.roles],
                    "last_login": user.last_login,
                    "created_at": user.created_at,
                    "two_factor_enabled": user.two_factor_enabled,
                    "two_factor_secret": user.two_factor_secret,
                    "is_active": user.is_active,
                    "email_verified": user.email_verified,
                    "meta": user.meta
                }
                
                user_data.append(user_dict)
                
            with open(users_file, 'w') as f:
                json.dump(user_data, f, indent=2)
                
            logger.info(f"Saved {len(self._users)} users to storage")
        except Exception as e:
            logger.error(f"Error saving users: {str(e)}")
    
    def _hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hash a password with salt.
        
        Args:
            password: Password to hash
            salt: Optional salt, generated if not provided
            
        Returns:
            Tuple of (password_hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)
            
        # Combine password and salt, then hash with SHA-256
        combined = (password + salt).encode('utf-8')
        password_hash = hashlib.sha256(combined).hexdigest()
        
        return password_hash, salt
    
    def _validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        Validate password strength against policy.
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < self._password_min_length:
            return False, f"Password must be at least {self._password_min_length} characters long"
            
        if self._password_requires_uppercase and not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
            
        if self._password_requires_lowercase and not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
            
        if self._password_requires_digit and not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
            
        if self._password_requires_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
            
        return True, ""
    
    def register_user(self, 
                    username: str, 
                    email: str, 
                    password: str,
                    roles: List[UserRole] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Register a new user.
        
        Args:
            username: Username for the new user
            email: Email address for the new user
            password: Password for the new user
            roles: Optional list of roles for the user
            
        Returns:
            Tuple of (success, message, user_id)
        """
        with self._lock:
            # Validate inputs
            if not username or not email or not password:
                return False, "Username, email, and password are required", None
                
            # Check if username or email already exists
            if username.lower() in self._username_to_id:
                return False, "Username already exists", None
                
            if email.lower() in self._email_to_id:
                return False, "Email already exists", None
                
            # Validate password strength
            is_valid, error_message = self._validate_password_strength(password)
            if not is_valid:
                return False, error_message, None
                
            # Validate email format
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                return False, "Invalid email format", None
                
            # Hash password
            password_hash, salt = self._hash_password(password)
            
            # Create user
            user_id = str(uuid.uuid4())
            
            user = User(
                id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                salt=salt,
                roles=roles or [UserRole.USER],
                created_at=time.time(),
                is_active=True,
                email_verified=False
            )
            
            # Store user
            self._users[user_id] = user
            self._username_to_id[username.lower()] = user.id
            self._email_to_id[email.lower()] = user.id
            
            # Save users to storage
            self._save_users()
            
            return True, "User registered successfully", user_id
    
    def authenticate(self, 
                   username_or_email: str, 
                   password: str) -> Tuple[bool, str, Optional[str]]:
        """
        Authenticate a user.
        
        Args:
            username_or_email: Username or email of the user
            password: Password to verify
            
        Returns:
            Tuple of (success, message, session_token)
        """
        with self._lock:
            # Find the user
            user_id = None
            
            if '@' in username_or_email:
                # Treat as email
                user_id = self._email_to_id.get(username_or_email.lower())
            else:
                # Treat as username
                user_id = self._username_to_id.get(username_or_email.lower())
                
            if not user_id:
                return False, "User not found", None
                
            user = self._users.get(user_id)
            
            if not user or not user.is_active:
                return False, "User not found or inactive", None
                
            # Verify password
            password_hash, _ = self._hash_password(password, user.salt)
            
            if password_hash != user.password_hash:
                return False, "Invalid password", None
                
            # Create session
            session_token = self._create_session(user)
            
            # Update last login
            user.last_login = time.time()
            self._save_users()
            
            return True, "Authentication successful", session_token
    
    def _create_session(self, user: User) -> str:
        """
        Create a new session for a user.
        
        Args:
            user: User to create session for
            
        Returns:
            Session token
        """
        if not JWT_AVAILABLE:
            # Fallback to simple session token
            session_token = secrets.token_hex(32)
            
            self._sessions[session_token] = {
                "user_id": user.id,
                "created_at": time.time(),
                "expires_at": time.time() + 86400  # 24 hours
            }
            
            return session_token
            
        # Create JWT token
        payload = {
            "sub": user.id,
            "name": user.username,
            "roles": [role.value for role in user.roles],
            "iat": int(time.time()),
            "exp": int(time.time() + 86400)  # 24 hours
        }
        
        token = jwt.encode(payload, self._jwt_secret, algorithm="HS256")
        
        return token
    
    def verify_session(self, session_token: str) -> Tuple[bool, Optional[User]]:
        """
        Verify a session token.
        
        Args:
            session_token: Session token to verify
            
        Returns:
            Tuple of (is_valid, user)
        """
        if not session_token:
            return False, None
            
        if JWT_AVAILABLE:
            try:
                # Verify JWT token
                payload = jwt.decode(session_token, self._jwt_secret, algorithms=["HS256"])
                
                user_id = payload.get("sub")
                if not user_id or user_id not in self._users:
                    return False, None
                    
                return True, self._users[user_id]
            except Exception as e:
                logger.warning(f"Error verifying JWT token: {str(e)}")
                return False, None
        else:
            # Fallback to simple session verification
            if session_token not in self._sessions:
                return False, None
                
            session = self._sessions[session_token]
            
            # Check if session has expired
            if session["expires_at"] < time.time():
                del self._sessions[session_token]
                return False, None
                
            user_id = session["user_id"]
            if user_id not in self._users:
                return False, None
                
            return True, self._users[user_id]
    
    def invalidate_session(self, session_token: str) -> bool:
        """
        Invalidate a session.
        
        Args:
            session_token: Session token to invalidate
            
        Returns:
            True if the session was invalidated, False otherwise
        """
        if JWT_AVAILABLE:
            # JWT tokens can't be invalidated directly
            # In a real implementation, you would maintain a blacklist of revoked tokens
            return True
        else:
            # Simple session invalidation
            if session_token in self._sessions:
                del self._sessions[session_token]
                return True
                
            return False
    
    def encrypt_data(self, data: Union[str, bytes]) -> Optional[bytes]:
        """
        Encrypt data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data as bytes, or None if encryption failed
        """
        if not ENCRYPTION_AVAILABLE or not self._encryption_key:
            logger.warning("Encryption not available")
            return None
            
        try:
            fernet = Fernet(self._encryption_key)
            
            if isinstance(data, str):
                data = data.encode('utf-8')
                
            return fernet.encrypt(data)
        except Exception as e:
            logger.error(f"Error encrypting data: {str(e)}")
            return None
    
    def decrypt_data(self, encrypted_data: bytes) -> Optional[bytes]:
        """
        Decrypt data.
        
        Args:
            encrypted_data: Encrypted data to decrypt
            
        Returns:
            Decrypted data as bytes, or None if decryption failed
        """
        if not ENCRYPTION_AVAILABLE or not self._encryption_key:
            logger.warning("Encryption not available")
            return None
            
        try:
            fernet = Fernet(self._encryption_key)
            return fernet.decrypt(encrypted_data)
        except Exception as e:
            logger.error(f"Error decrypting data: {str(e)}")
            return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            user_id: ID of the user to get
            
        Returns:
            User object or None if not found
        """
        return self._users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            username: Username of the user to get
            
        Returns:
            User object or None if not found
        """
        user_id = self._username_to_id.get(username.lower())
        if not user_id:
            return None
            
        return self._users.get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            email: Email of the user to get
            
        Returns:
            User object or None if not found
        """
        user_id = self._email_to_id.get(email.lower())
        if not user_id:
            return None
            
        return self._users.get(user_id)
    
    def update_user(self, user: User) -> bool:
        """
        Update a user.
        
        Args:
            user: User object to update
            
        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            if user.id not in self._users:
                return False
                
            # Check if username or email would cause a conflict
            existing_username_id = self._username_to_id.get(user.username.lower())
            if existing_username_id and existing_username_id != user.id:
                return False
                
            existing_email_id = self._email_to_id.get(user.email.lower())
            if existing_email_id and existing_email_id != user.id:
                return False
                
            # Update mapping dictionaries
            old_user = self._users[user.id]
            
            if old_user.username.lower() != user.username.lower():
                del self._username_to_id[old_user.username.lower()]
                self._username_to_id[user.username.lower()] = user.id
                
            if old_user.email.lower() != user.email.lower():
                del self._email_to_id[old_user.email.lower()]
                self._email_to_id[user.email.lower()] = user.id
                
            # Update user
            self._users[user.id] = user
            
            # Save users to storage
            self._save_users()
            
            return True
    
    def change_password(self, 
                      user_id: str, 
                      current_password: str, 
                      new_password: str) -> Tuple[bool, str]:
        """
        Change a user's password.
        
        Args:
            user_id: ID of the user to change password for
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            Tuple of (success, message)
        """
        with self._lock:
            user = self._users.get(user_id)
            if not user:
                return False, "User not found"
                
            # Verify current password
            password_hash, _ = self._hash_password(current_password, user.salt)
            
            if password_hash != user.password_hash:
                return False, "Current password is incorrect"
                
            # Validate new password strength
            is_valid, error_message = self._validate_password_strength(new_password)
            if not is_valid:
                return False, error_message
                
            # Set new password
            password_hash, salt = self._hash_password(new_password)
            
            user.password_hash = password_hash
            user.salt = salt
            
            # Save users to storage
            self._save_users()
            
            return True, "Password changed successfully"
    
    def reset_password(self, email: str) -> Tuple[bool, str]:
        """
        Initiate password reset process.
        
        In a real implementation, this would send an email with a reset link.
        For simplicity, this demo version just generates a new password.
        
        Args:
            email: Email of the user to reset password for
            
        Returns:
            Tuple of (success, message)
        """
        with self._lock:
            user_id = self._email_to_id.get(email.lower())
            if not user_id:
                # Don't reveal if the email exists
                return True, "If the email exists, a password reset link has been sent"
                
            user = self._users.get(user_id)
            
            if not user or not user.is_active:
                return True, "If the email exists, a password reset link has been sent"
                
            # In a real implementation, send an email with a reset link
            # For this demo, just log the action
            logger.info(f"Password reset requested for {email}")
            
            return True, "If the email exists, a password reset link has been sent"
    
    def set_password_policy(self,
                          min_length: int = 8,
                          requires_uppercase: bool = True,
                          requires_lowercase: bool = True,
                          requires_digit: bool = True,
                          requires_special: bool = True) -> None:
        """
        Set the password policy.
        
        Args:
            min_length: Minimum password length
            requires_uppercase: Whether passwords must contain uppercase letters
            requires_lowercase: Whether passwords must contain lowercase letters
            requires_digit: Whether passwords must contain digits
            requires_special: Whether passwords must contain special characters
        """
        self._password_min_length = min_length
        self._password_requires_uppercase = requires_uppercase
        self._password_requires_lowercase = requires_lowercase
        self._password_requires_digit = requires_digit
        self._password_requires_special = requires_special


# Global instance
security_manager = SecurityManager()

def get_security_manager() -> SecurityManager:
    """
    Get the global security manager instance.
    
    Returns:
        SecurityManager instance
    """
    return security_manager

def authenticate(username_or_email: str, password: str) -> Tuple[bool, str, Optional[str]]:
    """
    Authenticate a user.
    
    Args:
        username_or_email: Username or email of the user
        password: Password to verify
        
    Returns:
        Tuple of (success, message, session_token)
    """
    return security_manager.authenticate(username_or_email, password)

def verify_session(session_token: str) -> Tuple[bool, Optional[User]]:
    """
    Verify a session token.
    
    Args:
        session_token: Session token to verify
        
    Returns:
        Tuple of (is_valid, user)
    """
    return security_manager.verify_session(session_token)

def requires_auth(func: Callable):
    """
    Decorator to require authentication for a function.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract session_token from kwargs
        session_token = kwargs.get('session_token')
        
        if not session_token:
            raise ValueError("Authentication required")
            
        is_valid, user = security_manager.verify_session(session_token)
        
        if not is_valid or not user:
            raise ValueError("Invalid or expired session")
            
        # Add user to kwargs for the decorated function
        kwargs['user'] = user
        
        return func(*args, **kwargs)
    return wrapper

def requires_role(role: UserRole):
    """
    Decorator to require a specific role for a function.
    
    Args:
        role: Role required
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract session_token from kwargs
            session_token = kwargs.get('session_token')
            
            if not session_token:
                raise ValueError("Authentication required")
                
            is_valid, user = security_manager.verify_session(session_token)
            
            if not is_valid or not user:
                raise ValueError("Invalid or expired session")
                
            if not user.has_role(role):
                raise ValueError(f"Required role not found: {role.value}")
                
            # Add user to kwargs for the decorated function
            kwargs['user'] = user
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def requires_permission(resource: str, level: PermissionLevel):
    """
    Decorator to require a specific permission for a function.
    
    Args:
        resource: Resource to check permissions for
        level: Permission level required
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract session_token from kwargs
            session_token = kwargs.get('session_token')
            
            if not session_token:
                raise ValueError("Authentication required")
                
            is_valid, user = security_manager.verify_session(session_token)
            
            if not is_valid or not user:
                raise ValueError("Invalid or expired session")
                
            if not user.has_permission(resource, level):
                raise ValueError(f"Required permission not found: {level.value} on {resource}")
                
            # Add user to kwargs for the decorated function
            kwargs['user'] = user
            
            return func(*args, **kwargs)
        return wrapper
    return decorator 