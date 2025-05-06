"""
Integration Tests for Community Features of MT 9 EMA Backtester.

This module contains integration tests for community features including
trading setup sharing, forums, and trading signals. These tests simulate
user interactions to ensure the features work correctly together.
"""

import os
import pytest
import uuid
import json
import datetime
from unittest.mock import patch, MagicMock

# Import community features (update these imports based on actual implementation)
from mtfema_backtester.community import forums, sharing, signals
from mtfema_backtester.utils import security, feature_flags
from mtfema_backtester.utils.feature_flags import FeatureState

# Fixtures for testing

@pytest.fixture
def setup_feature_flags():
    """Set up feature flags for testing."""
    # Get the feature flag manager
    ff_manager = feature_flags.get_feature_flags()
    
    # Enable all community features for testing
    ff_manager.set_override("community.forums", FeatureState.ON)
    ff_manager.set_override("community.signals", FeatureState.ON)
    ff_manager.set_override("community.sharing", FeatureState.ON)
    ff_manager.set_override("community.profiles", FeatureState.ON)
    
    yield
    
    # Reset feature flags after test
    ff_manager.reset_override("community.forums")
    ff_manager.reset_override("community.signals")
    ff_manager.reset_override("community.sharing")
    ff_manager.reset_override("community.profiles")


@pytest.fixture
def mock_security_manager():
    """Mock security manager for user authentication."""
    with patch('mtfema_backtester.utils.security.SecurityManager') as mock_manager:
        # Create mock users
        user1 = MagicMock()
        user1.id = str(uuid.uuid4())
        user1.username = "testuser1"
        user1.email = "testuser1@example.com"
        user1.has_role.return_value = True
        user1.has_permission.return_value = True
        
        user2 = MagicMock()
        user2.id = str(uuid.uuid4())
        user2.username = "testuser2"
        user2.email = "testuser2@example.com"
        user2.has_role.return_value = True
        user2.has_permission.return_value = True
        
        # Mock authentication and session verification
        mock_instance = mock_manager.return_value
        mock_instance.authenticate.return_value = (True, "Success", "mock_session_token")
        mock_instance.verify_session.return_value = (True, user1)
        mock_instance.get_user_by_id.side_effect = lambda id: user1 if id == user1.id else user2 if id == user2.id else None
        
        yield {"manager": mock_instance, "user1": user1, "user2": user2}


@pytest.fixture
def mock_database():
    """Mock database for community features."""
    # Create in-memory temporary storage
    db = {
        "forum_categories": [],
        "forum_topics": [],
        "forum_posts": [],
        "trading_setups": [],
        "setup_comments": [],
        "setup_likes": [],
        "trading_signals": [],
        "signal_subscriptions": []
    }
    
    yield db


class TestForumFeatures:
    """Integration tests for forum features."""
    
    @pytest.mark.integration
    def test_create_forum_category_and_topic(self, setup_feature_flags, mock_security_manager, mock_database):
        """Test creating a forum category and topic."""
        user = mock_security_manager["user1"]
        
        # Mock forum module database access
        with patch.object(forums, 'db', mock_database):
            # Create a forum category
            category_data = {
                "name": "Trading Strategies",
                "description": "Discuss different trading strategies",
                "slug": "trading-strategies"
            }
            
            category_id = forums.create_category(
                category_data, 
                user_id=user.id, 
                session_token="mock_session_token"
            )
            
            # Create a topic in the category
            topic_data = {
                "category_id": category_id,
                "title": "9 EMA Strategy Discussion",
                "content": "Let's discuss the 9 EMA strategy effectiveness."
            }
            
            topic_id = forums.create_topic(
                topic_data, 
                user_id=user.id, 
                session_token="mock_session_token"
            )
            
            # Create a reply to the topic
            post_data = {
                "topic_id": topic_id,
                "content": "I've found the 9 EMA strategy works well in trending markets."
            }
            
            post_id = forums.create_post(
                post_data, 
                user_id=user.id, 
                session_token="mock_session_token"
            )
            
            # Verify data was created correctly
            assert len(mock_database["forum_categories"]) == 1
            assert mock_database["forum_categories"][0]["name"] == "Trading Strategies"
            
            assert len(mock_database["forum_topics"]) == 1
            assert mock_database["forum_topics"][0]["title"] == "9 EMA Strategy Discussion"
            
            assert len(mock_database["forum_posts"]) == 2  # Initial post + reply
            assert mock_database["forum_posts"][1]["content"] == "I've found the 9 EMA strategy works well in trending markets."
    
    @pytest.mark.integration
    def test_forum_category_permissions(self, setup_feature_flags, mock_security_manager, mock_database):
        """Test forum category permissions."""
        admin_user = mock_security_manager["user1"]
        regular_user = mock_security_manager["user2"]
        
        # Set up different permissions for users
        admin_user.has_permission.return_value = True
        regular_user.has_permission.return_value = False
        
        # Mock forum module database access
        with patch.object(forums, 'db', mock_database):
            # Create a private forum category
            category_data = {
                "name": "Admin Only",
                "description": "Category for admins only",
                "slug": "admin-only",
                "is_private": True
            }
            
            # Admin can create private category
            category_id = forums.create_category(
                category_data, 
                user_id=admin_user.id, 
                session_token="mock_session_token"
            )
            
            # Temporarily change mock to return regular user
            with patch.object(mock_security_manager["manager"], 'verify_session', return_value=(True, regular_user)):
                # Regular user should not be able to create a topic in private category
                topic_data = {
                    "category_id": category_id,
                    "title": "Test Topic",
                    "content": "Test content"
                }
                
                with pytest.raises(Exception) as excinfo:
                    forums.create_topic(
                        topic_data, 
                        user_id=regular_user.id, 
                        session_token="mock_session_token"
                    )
                
                assert "permission" in str(excinfo.value).lower()


class TestTradingSetupSharing:
    """Integration tests for trading setup sharing."""
    
    @pytest.mark.integration
    def test_create_and_like_setup(self, setup_feature_flags, mock_security_manager, mock_database):
        """Test creating a trading setup and liking it."""
        user1 = mock_security_manager["user1"]
        user2 = mock_security_manager["user2"]
        
        # Mock sharing module database access
        with patch.object(sharing, 'db', mock_database):
            # Create a trading setup
            setup_data = {
                "title": "9 EMA Extension Strategy",
                "description": "My implementation of the 9 EMA extension strategy",
                "symbol": "ES",
                "timeframes": "5m,15m,1h",
                "strategy_parameters": {
                    "ema_period": 9,
                    "extension_threshold": 1.5,
                    "reclamation_threshold": 0.3
                },
                "risk_parameters": {
                    "risk_per_trade": 1.0,
                    "max_drawdown": 5.0
                },
                "visibility": "public"
            }
            
            setup_id = sharing.create_setup(
                setup_data, 
                user_id=user1.id, 
                session_token="mock_session_token"
            )
            
            # User2 likes the setup
            with patch.object(mock_security_manager["manager"], 'verify_session', return_value=(True, user2)):
                sharing.like_setup(
                    setup_id, 
                    user_id=user2.id, 
                    session_token="mock_session_token"
                )
                
                # User2 comments on the setup
                comment_data = {
                    "setup_id": setup_id,
                    "content": "Great setup! I've had success with similar parameters."
                }
                
                comment_id = sharing.create_comment(
                    comment_data, 
                    user_id=user2.id, 
                    session_token="mock_session_token"
                )
            
            # Verify data was created correctly
            assert len(mock_database["trading_setups"]) == 1
            assert mock_database["trading_setups"][0]["title"] == "9 EMA Extension Strategy"
            
            assert len(mock_database["setup_likes"]) == 1
            assert mock_database["setup_likes"][0]["user_id"] == user2.id
            
            assert len(mock_database["setup_comments"]) == 1
            assert mock_database["setup_comments"][0]["content"] == "Great setup! I've had success with similar parameters."
    
    @pytest.mark.integration
    def test_setup_visibility_permissions(self, setup_feature_flags, mock_security_manager, mock_database):
        """Test trading setup visibility permissions."""
        user1 = mock_security_manager["user1"]
        user2 = mock_security_manager["user2"]
        
        # Mock sharing module database access
        with patch.object(sharing, 'db', mock_database):
            # Create a private trading setup
            setup_data = {
                "title": "My Secret Strategy",
                "description": "Private strategy details",
                "symbol": "NQ",
                "timeframes": "1h,4h",
                "strategy_parameters": {
                    "ema_period": 9,
                    "extension_threshold": 2.0
                },
                "visibility": "private"
            }
            
            setup_id = sharing.create_setup(
                setup_data, 
                user_id=user1.id, 
                session_token="mock_session_token"
            )
            
            # User2 tries to view the private setup
            with patch.object(mock_security_manager["manager"], 'verify_session', return_value=(True, user2)):
                with pytest.raises(Exception) as excinfo:
                    sharing.get_setup(
                        setup_id, 
                        user_id=user2.id, 
                        session_token="mock_session_token"
                    )
                
                assert "permission" in str(excinfo.value).lower() or "private" in str(excinfo.value).lower()


class TestTradingSignals:
    """Integration tests for trading signals."""
    
    @pytest.mark.integration
    def test_create_and_subscribe_to_signal(self, setup_feature_flags, mock_security_manager, mock_database):
        """Test creating a trading signal and subscribing to it."""
        provider = mock_security_manager["user1"]
        subscriber = mock_security_manager["user2"]
        
        # Mock signals module database access
        with patch.object(signals, 'db', mock_database):
            # Create a trading signal
            signal_data = {
                "title": "ES Long Opportunity",
                "description": "ES is showing a bullish 9 EMA extension setup",
                "symbol": "ES",
                "timeframe": "1h",
                "direction": "long",
                "entry_price": 4500.50,
                "stop_loss": 4480.25,
                "take_profit_levels": [
                    {"price": 4520.75, "percentage": 50},
                    {"price": 4540.00, "percentage": 50}
                ],
                "expiry_time": (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()
            }
            
            signal_id = signals.create_signal(
                signal_data, 
                user_id=provider.id, 
                session_token="mock_session_token"
            )
            
            # User2 subscribes to user1's signals
            with patch.object(mock_security_manager["manager"], 'verify_session', return_value=(True, subscriber)):
                signals.subscribe_to_provider(
                    provider_id=provider.id, 
                    user_id=subscriber.id, 
                    session_token="mock_session_token"
                )
                
                # Get signals from subscriptions
                subscribed_signals = signals.get_signals_from_subscriptions(
                    user_id=subscriber.id, 
                    session_token="mock_session_token"
                )
            
            # Verify data was created correctly
            assert len(mock_database["trading_signals"]) == 1
            assert mock_database["trading_signals"][0]["title"] == "ES Long Opportunity"
            
            assert len(mock_database["signal_subscriptions"]) == 1
            assert mock_database["signal_subscriptions"][0]["provider_id"] == provider.id
            assert mock_database["signal_subscriptions"][0]["user_id"] == subscriber.id
            
            assert len(subscribed_signals) == 1
            assert subscribed_signals[0]["id"] == signal_id
    
    @pytest.mark.integration
    def test_signal_update_and_completion(self, setup_feature_flags, mock_security_manager, mock_database):
        """Test updating a trading signal and marking it as completed."""
        provider = mock_security_manager["user1"]
        
        # Mock signals module database access
        with patch.object(signals, 'db', mock_database):
            # Create a trading signal
            signal_data = {
                "title": "NQ Short Opportunity",
                "description": "NQ is showing a bearish 9 EMA extension setup",
                "symbol": "NQ",
                "timeframe": "1h",
                "direction": "short",
                "entry_price": 15200.50,
                "stop_loss": 15250.75,
                "take_profit_levels": [
                    {"price": 15150.00, "percentage": 100}
                ]
            }
            
            signal_id = signals.create_signal(
                signal_data, 
                user_id=provider.id, 
                session_token="mock_session_token"
            )
            
            # Update signal to triggered state
            update_data = {
                "status": "triggered",
                "triggered_at": datetime.datetime.now().isoformat(),
                "notes": "Entry triggered at 15195.25"
            }
            
            signals.update_signal(
                signal_id,
                update_data,
                user_id=provider.id,
                session_token="mock_session_token"
            )
            
            # Mark signal as completed
            complete_data = {
                "status": "completed",
                "completed_at": datetime.datetime.now().isoformat(),
                "result": "win",
                "profit_loss": 0.75,  # 0.75% profit
                "notes": "Target reached, all positions closed"
            }
            
            signals.update_signal(
                signal_id,
                complete_data,
                user_id=provider.id,
                session_token="mock_session_token"
            )
            
            # Get the updated signal
            updated_signal = signals.get_signal(
                signal_id,
                user_id=provider.id,
                session_token="mock_session_token"
            )
            
            # Verify data was updated correctly
            assert updated_signal["status"] == "completed"
            assert updated_signal["result"] == "win"
            assert updated_signal["profit_loss"] == 0.75


class TestCommunityIntegration:
    """Integration tests for multiple community features together."""
    
    @pytest.mark.integration
    def test_forum_setup_signals_integration(self, setup_feature_flags, mock_security_manager, mock_database):
        """Test integration between forums, trading setups, and signals."""
        user1 = mock_security_manager["user1"]
        user2 = mock_security_manager["user2"]
        
        # Mock all modules to use the same database
        with patch.object(forums, 'db', mock_database), \
             patch.object(sharing, 'db', mock_database), \
             patch.object(signals, 'db', mock_database):
            
            # 1. User1 creates a trading setup
            setup_data = {
                "title": "9 EMA Multi-timeframe Strategy",
                "description": "A complete multi-timeframe 9 EMA strategy",
                "symbol": "ES",
                "timeframes": "5m,15m,1h,4h",
                "strategy_parameters": json.dumps({
                    "ema_period": 9,
                    "extension_threshold": 1.75,
                    "pullback_threshold": 0.5
                }),
                "visibility": "public"
            }
            
            setup_id = sharing.create_setup(
                setup_data, 
                user_id=user1.id, 
                session_token="mock_session_token"
            )
            
            # 2. User1 creates a forum category and topic to discuss the setup
            category_data = {
                "name": "Strategy Discussions",
                "description": "Discuss trading strategies",
                "slug": "strategy-discussions"
            }
            
            category_id = forums.create_category(
                category_data, 
                user_id=user1.id, 
                session_token="mock_session_token"
            )
            
            topic_data = {
                "category_id": category_id,
                "title": "My 9 EMA Multi-timeframe Strategy",
                "content": f"I've shared a new strategy at setup ID: {setup_id}. Let's discuss it here."
            }
            
            topic_id = forums.create_topic(
                topic_data, 
                user_id=user1.id, 
                session_token="mock_session_token"
            )
            
            # 3. User2 replies to the topic
            with patch.object(mock_security_manager["manager"], 'verify_session', return_value=(True, user2)):
                post_data = {
                    "topic_id": topic_id,
                    "content": f"I like your setup! I've tried it and it works well."
                }
                
                forums.create_post(
                    post_data, 
                    user_id=user2.id, 
                    session_token="mock_session_token"
                )
                
                # 4. User2 likes the setup
                sharing.like_setup(
                    setup_id, 
                    user_id=user2.id, 
                    session_token="mock_session_token"
                )
                
                # 5. User2 subscribes to user1's signals
                signals.subscribe_to_provider(
                    provider_id=user1.id, 
                    user_id=user2.id, 
                    session_token="mock_session_token"
                )
            
            # 6. User1 creates a signal based on the setup
            signal_data = {
                "title": "ES Long Based on 9 EMA Strategy",
                "description": "Signal based on my 9 EMA multi-timeframe strategy",
                "symbol": "ES",
                "timeframe": "1h",
                "direction": "long",
                "entry_price": 4525.75,
                "stop_loss": 4510.25,
                "take_profit_levels": [
                    {"price": 4545.50, "percentage": 50},
                    {"price": 4565.25, "percentage": 50}
                ],
                "setup_id": setup_id
            }
            
            signal_id = signals.create_signal(
                signal_data, 
                user_id=user1.id, 
                session_token="mock_session_token"
            )
            
            # 7. User2 checks signals from subscriptions
            with patch.object(mock_security_manager["manager"], 'verify_session', return_value=(True, user2)):
                subscribed_signals = signals.get_signals_from_subscriptions(
                    user_id=user2.id, 
                    session_token="mock_session_token"
                )
                
                # 8. User2 adds a comment about the signal in the forum
                post_data = {
                    "topic_id": topic_id,
                    "content": f"I received your signal (ID: {signal_id}). Looking forward to the results!"
                }
                
                forums.create_post(
                    post_data, 
                    user_id=user2.id, 
                    session_token="mock_session_token"
                )
            
            # Verify integration worked correctly
            assert len(mock_database["trading_setups"]) == 1
            assert len(mock_database["forum_topics"]) == 1
            assert len(mock_database["forum_posts"]) >= 3  # Initial post + 2 replies
            assert len(mock_database["setup_likes"]) == 1
            assert len(mock_database["signal_subscriptions"]) == 1
            assert len(mock_database["trading_signals"]) == 1
            
            # Verify the signal references the setup
            assert mock_database["trading_signals"][0]["setup_id"] == setup_id
            
            # Verify user2 received the signal
            assert len(subscribed_signals) == 1
            assert subscribed_signals[0]["id"] == signal_id 