        elif metric == "signals_viewed":
            analytics["signals_viewed"] += value
            
        elif metric == "signals_acted_on":
            analytics["signals_acted_on"] += value
        
        elif metric == "engagement_rate":
            # Direct setting for engagement rate
            analytics["engagement_rate"] = value
        
        else:
            # For custom metrics
            analytics[metric] = value
        
        # Calculate engagement rate
        if analytics["signals_received"] > 0:
            analytics["engagement_rate"] = analytics["signals_acted_on"] / analytics["signals_received"]
        
        # Update timestamp
        analytics["last_updated"] = datetime.now().isoformat()
    
    def _load_data(self):
        """
        Load subscription data from storage.
        """
        if not self.storage_path:
            logger.warning("No storage path set, running in-memory only")
            return
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        # Try to load subscriptions
        subscriptions_path = f"{self.storage_path}/subscriptions.json"
        if os.path.exists(subscriptions_path):
            try:
                with open(subscriptions_path, 'r') as f:
                    self.subscriptions = json.load(f)
                logger.info(f"Loaded {len(self.subscriptions)} subscriptions")
            except Exception as e:
                logger.error(f"Error loading subscriptions: {e}")
        
        # Try to load user subscriptions mapping
        user_subs_path = f"{self.storage_path}/user_subscriptions.json"
        if os.path.exists(user_subs_path):
            try:
                with open(user_subs_path, 'r') as f:
                    self.user_subscriptions = json.load(f)
                logger.info(f"Loaded user subscriptions for {len(self.user_subscriptions)} users")
            except Exception as e:
                logger.error(f"Error loading user subscriptions: {e}")
        
        # Try to load provider subscribers mapping
        provider_subs_path = f"{self.storage_path}/provider_subscribers.json"
        if os.path.exists(provider_subs_path):
            try:
                with open(provider_subs_path, 'r') as f:
                    self.provider_subscribers = json.load(f)
                logger.info(f"Loaded provider subscribers for {len(self.provider_subscribers)} providers")
            except Exception as e:
                logger.error(f"Error loading provider subscribers: {e}")
        
        # Try to load pending notifications
        notifications_path = f"{self.storage_path}/pending_notifications.json"
        if os.path.exists(notifications_path):
            try:
                with open(notifications_path, 'r') as f:
                    self.pending_notifications = json.load(f)
                logger.info(f"Loaded pending notifications for {len(self.pending_notifications)} users")
            except Exception as e:
                logger.error(f"Error loading pending notifications: {e}")
        
        # Try to load analytics
        analytics_path = f"{self.storage_path}/subscription_analytics.json"
        if os.path.exists(analytics_path):
            try:
                with open(analytics_path, 'r') as f:
                    self.subscription_analytics = json.load(f)
                logger.info(f"Loaded analytics for {len(self.subscription_analytics)} subscriptions")
            except Exception as e:
                logger.error(f"Error loading subscription analytics: {e}")
    
    def _save_data(self):
        """
        Save subscription data to storage.
        """
        if not self.storage_path:
            logger.info("No storage path set, not saving data")
            return
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        try:
            # Save subscriptions
            with open(f"{self.storage_path}/subscriptions.json", 'w') as f:
                json.dump(self.subscriptions, f, indent=2)
            
            # Save user subscriptions mapping
            with open(f"{self.storage_path}/user_subscriptions.json", 'w') as f:
                json.dump(self.user_subscriptions, f, indent=2)
            
            # Save provider subscribers mapping
            with open(f"{self.storage_path}/provider_subscribers.json", 'w') as f:
                json.dump(self.provider_subscribers, f, indent=2)
            
            # Save pending notifications
            with open(f"{self.storage_path}/pending_notifications.json", 'w') as f:
                json.dump(self.pending_notifications, f, indent=2)
            
            # Save analytics
            with open(f"{self.storage_path}/subscription_analytics.json", 'w') as f:
                json.dump(self.subscription_analytics, f, indent=2)
            
            logger.debug("Saved subscription data to disk")
        except Exception as e:
            logger.error(f"Error saving subscription data: {e}")


# Helper functions for easier access

def get_subscription_manager() -> SignalSubscription:
    """
    Get the global signal subscription manager instance.
    
    Returns:
        SignalSubscription instance
    """
    return SignalSubscription()

def subscribe(user_id: str, 
             provider_id: str, 
             filters: Optional[Dict[str, Any]] = None,
             notification_preferences: Optional[Dict[str, Any]] = None) -> str:
    """
    Subscribe a user to signals from a provider.
    
    Args:
        user_id: ID of the subscribing user
        provider_id: ID of the signal provider
        filters: Optional filters for which signals to receive
        notification_preferences: How the user wants to be notified
            
    Returns:
        ID of the new subscription
    """
    manager = get_subscription_manager()
    return manager.subscribe(user_id, provider_id, filters, notification_preferences)

def unsubscribe(user_id: str, provider_id: str) -> bool:
    """
    Unsubscribe a user from a provider's signals.
    
    Args:
        user_id: ID of the subscribing user
        provider_id: ID of the signal provider
        
    Returns:
        Whether the unsubscription was successful
    """
    manager = get_subscription_manager()
    return manager.unsubscribe(user_id, provider_id)

def process_new_signal(signal_data: Dict[str, Any]) -> int:
    """
    Process a new signal and notify subscribers.
    
    Args:
        signal_data: Data about the new signal
            
    Returns:
        Number of notifications sent
    """
    manager = get_subscription_manager()
    return manager.process_new_signal(signal_data)

def get_user_subscriptions(user_id: str) -> List[Dict[str, Any]]:
    """
    Get all subscriptions for a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        List of subscription objects
    """
    manager = get_subscription_manager()
    return manager.get_user_subscriptions(user_id)

def get_pending_notifications(user_id: str, mark_as_read: bool = False) -> List[Dict[str, Any]]:
    """
    Get pending notifications for a user.
    
    Args:
        user_id: ID of the user
        mark_as_read: Whether to mark retrieved notifications as read
        
    Returns:
        List of notification objects
    """
    manager = get_subscription_manager()
    return manager.get_pending_notifications(user_id, mark_as_read)
