"""
Example of integrating community features with the reputation system.

This example demonstrates how to use the community manager to integrate
the forum, signals, trading setup sharing, and reputation system.
"""

import os
import logging
from datetime import datetime
from mtfema_backtester.community import CommunityManager
from mtfema_backtester.community.reputation import get_user_reputation, get_user_badges, ActionType
from mtfema_backtester.community.feature_flags import get_feature_flags

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demonstrate_community_integration():
    """
    Demonstrate integration of community features with reputation system.
    """
    # Check if community features are enabled
    feature_flags = get_feature_flags()
    if not feature_flags.is_enabled("community.forums") and not feature_flags.is_enabled("community.signals"):
        logger.warning("Community features are disabled. Enable them in settings or environment variables.")
        logger.info("To enable: set MTFEMA_FEATURE_FORUMS=true and MTFEMA_FEATURE_SIGNALS=true")
        return
    
    # Initialize community manager
    storage_path = os.path.join(os.path.expanduser("~"), ".mtfema", "community_example")
    community = CommunityManager(storage_path=storage_path)
    
    # Login to community platform (simulated in this example)
    username = "example_user"
    password = "secure_password"  # In a real app, use secure password handling
    
    if not community.login(username, password):
        logger.error("Failed to login to community platform")
        return
    
    user_id = community.user_id
    logger.info(f"Logged in as {username} (User ID: {user_id})")
    
    # 1. Create a forum post - this automatically awards reputation points
    logger.info("\n--- CREATING FORUM POST ---")
    forum_post = community.create_forum_post(
        title="MT 9 EMA Strategy Refinement",
        content="I've been testing a variation of the MT 9 EMA strategy that uses additional confirmation indicators. Here are my results...",
        category="strategy-discussion",
        tags=["ema", "strategy", "indicators"]
    )
    
    if forum_post:
        logger.info(f"Created forum post: {forum_post.title}")
        
        # Display updated reputation after creating post
        reputation = get_user_reputation(user_id)
        logger.info(f"Current reputation: {reputation['points']} points (Level {reputation['level']})")
        
        badges = get_user_badges(user_id)
        if badges:
            logger.info(f"Badges earned: {', '.join([f'{b['icon']} {b['name']}' for b in badges])}")
    
    # 2. Create and share a trading signal - also awards reputation points
    logger.info("\n--- CREATING TRADING SIGNAL ---")
    signal = community.create_signal(
        symbol="ES",
        direction="buy",
        entry_price=4500.50,
        stop_loss=4480.25,
        take_profit=4550.75,
        timeframe="1h",
        description="9 EMA reclamation after pullback, strong momentum",
        setup_type="MT9EMA",
        expiry_hours=24
    )
    
    if signal:
        logger.info(f"Created signal for {signal.symbol} {signal.direction} at {signal.entry_price}")
        
        # Display updated reputation after creating signal
        reputation = get_user_reputation(user_id)
        logger.info(f"Current reputation: {reputation['points']} points (Level {reputation['level']})")
        
        badges = get_user_badges(user_id)
        if badges:
            logger.info(f"Badges earned: {', '.join([f'{b['icon']} {b['name']}' for b in badges])}")
    
    # 3. Share a trading setup
    logger.info("\n--- SHARING TRADING SETUP ---")
    setup = {
        "symbol": "NQ",
        "timeframe": "15m",
        "setup_type": "MT9EMA",
        "direction": "sell",
        "entry_price": 15250.75,
        "stop_loss": 15300.50,
        "take_profit": 15150.00,
        "risk_reward": 2.01,
        "description": "Short at 9 EMA extension, multiple timeframe confirmation",
        "screenshot": None  # Would be a base64 encoded image in real usage
    }
    
    result = community.share_trading_setup(setup)
    
    if result.get("success", False):
        logger.info(f"Shared trading setup: {result.get('url')}")
        
        # Display updated reputation after sharing setup
        reputation = get_user_reputation(user_id)
        logger.info(f"Current reputation: {reputation['points']} points (Level {reputation['level']})")
        
        badges = get_user_badges(user_id)
        if badges:
            logger.info(f"Badges earned: {', '.join([f'{b['icon']} {b['name']}' for b in badges])}")
    
    # 4. Simulate a successful signal (normally this would happen over time)
    logger.info("\n--- SIMULATING SUCCESSFUL SIGNAL ---")
    logger.info("Fast-forwarding time to simulate a successful signal...")
    
    # In a real application, this would be triggered by an event when the signal is successful
    from mtfema_backtester.community.reputation import award_points
    award_points(user_id, ActionType.SIGNAL_SUCCESS.value, {"signal_id": signal.signal_id})
    
    # Display updated reputation after signal success
    reputation = get_user_reputation(user_id)
    logger.info(f"Signal was successful!")
    logger.info(f"Current reputation: {reputation['points']} points (Level {reputation['level']})")
    
    badges = get_user_badges(user_id)
    if badges:
        logger.info(f"Badges earned: {', '.join([f'{b['icon']} {b['name']}' for b in badges])}")
    
    # 5. Generate leaderboard
    logger.info("\n--- GENERATING LEADERBOARD ---")
    from mtfema_backtester.community.reputation import generate_leaderboard
    
    # Simulate additional users with reputation (in a real app, these would be real users)
    for i in range(1, 10):
        dummy_user_id = f"user_{i}"
        points = (10 - i) * 100  # First user has most points, descending from there
        for j in range(points // 10):
            award_points(dummy_user_id, ActionType.FORUM_POST_CREATE.value, {})
    
    # Generate the leaderboard
    leaderboard = generate_leaderboard(category="reputation", timeframe="all_time", limit=5)
    
    logger.info("Reputation Leaderboard (Top 5):")
    for entry in leaderboard:
        logger.info(f"#{entry['rank']}: User {entry['user_id']} - {entry['points']} points (Level {entry['level']})")
    
    # Find user's rank
    user_rank = None
    for entry in leaderboard:
        if entry['user_id'] == user_id:
            user_rank = entry['rank']
            break
    
    if user_rank:
        logger.info(f"Your rank: #{user_rank}")
    else:
        logger.info("Your rank: Outside top 5")
    
    # 6. Display community overview
    logger.info("\n--- COMMUNITY OVERVIEW ---")
    overview = community.get_community_overview()
    
    logger.info(f"Active users: {overview.get('active_users', 0)}")
    logger.info(f"Total forum posts: {overview.get('total_posts', 0)}")
    logger.info(f"Active signals: {overview.get('active_signals', 0)}")
    logger.info(f"Shared setups: {overview.get('shared_setups', 0)}")
    
    # Logout from community platform
    community.logout()
    logger.info("\nLogged out of community platform")


if __name__ == "__main__":
    demonstrate_community_integration() 