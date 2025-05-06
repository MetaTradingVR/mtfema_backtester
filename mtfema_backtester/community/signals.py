        try:
            with open(signals_file, 'r') as f:
                data = json.load(f)
                
                signals = []
                for signal_data in data:
                    signals.append(TradingSignal.from_dict(signal_data))
                
                return signals
                
        except Exception as e:
            logger.error(f"Error loading signals: {str(e)}")
            return []
    
    def _save_signals(self, signals: List[TradingSignal]):
        """Save signals to storage."""
        signals_file = os.path.join(self.storage_path, "signals.json")
        
        try:
            # Convert signals to dictionaries
            data = [signal.to_dict() for signal in signals]
            
            # Save to JSON file
            with open(signals_file, 'w') as f:
                json.dump(data, f, indent=4)
                
            # Update cache
            self.signals_cache = signals.copy()
            self.last_update = datetime.now()
            
        except Exception as e:
            logger.error(f"Error saving signals: {str(e)}")
    
    def fetch_community_signals(self, api_key: str, 
                              symbol: Optional[str] = None,
                              timeframe: Optional[str] = None,
                              limit: int = 50) -> List[TradingSignal]:
        """
        Fetch signals from the community platform.
        
        Args:
            api_key: API key for authentication
            symbol: Filter by symbol
            timeframe: Filter by timeframe
            limit: Maximum number of signals to retrieve
            
        Returns:
            List of TradingSignal objects
        """
        try:
            # In a real implementation, this would make an API call
            # Simulate API response with sample data
            signals = []
            
            # Generate some sample signals
            sample_symbols = ["ES", "NQ", "CL", "GC", "EURUSD", "AAPL", "MSFT"]
            sample_timeframes = ["5m", "15m", "1h", "4h", "1d"]
            sample_directions = ["buy", "sell"]
            
            for i in range(limit):
                sample_symbol = sample_symbols[i % len(sample_symbols)]
                
                # Skip if we're filtering by symbol and it doesn't match
                if symbol and symbol != sample_symbol:
                    continue
                
                sample_tf = sample_timeframes[i % len(sample_timeframes)]
                
                # Skip if we're filtering by timeframe and it doesn't match
                if timeframe and timeframe != sample_tf:
                    continue
                
                sample_direction = sample_directions[i % len(sample_directions)]
                sample_price = 100 + (i * 5)
                
                # Create sample timestamps
                now = datetime.now()
                created_at = now - timedelta(hours=i*2)
                expires_at = created_at + timedelta(hours=24)
                
                # Determine if signal should be expired based on creation time
                status = "active"
                result = None
                profit_pct = None
                
                if created_at < (now - timedelta(hours=20)):
                    # Some older signals should be executed
                    if i % 3 == 0:
                        status = "executed"
                        result = "win" if i % 2 == 0 else "loss"
                        profit_pct = 3.5 if result == "win" else -1.2
                
                signal_data = {
                    "signal_id": f"signal_{i}_{str(uuid.uuid4())[:8]}",
                    "user_id": f"user_{i % 10}",
                    "username": f"trader{i % 10}",
                    "symbol": sample_symbol,
                    "direction": sample_direction,
                    "entry_price": sample_price,
                    "stop_loss": sample_price * (0.95 if sample_direction == "buy" else 1.05),
                    "take_profit": sample_price * (1.15 if sample_direction == "buy" else 0.85),
                    "timeframe": sample_tf,
                    "created_at": created_at,
                    "expires_at": expires_at,
                    "description": f"MT 9 EMA extension setup on {sample_symbol} {sample_tf}",
                    "status": status,
                    "result": result,
                    "profit_pct": profit_pct,
                    "setup_type": "MT9EMA",
                    "risk_reward": 3.0
                }
                
                signal = TradingSignal.from_dict(signal_data)
                signals.append(signal)
            
            logger.info(f"Fetched {len(signals)} signals from community")
            return signals
            
        except Exception as e:
            logger.error(f"Error fetching community signals: {str(e)}")
            return []
    
    def get_user_performance(self, user_id: str) -> Dict[str, Any]:
        """
        Get performance statistics for a specific user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            # In a real implementation, this would make an API call
            # Simulate API response with sample data
            
            # Use user_id to seed random data generator for consistent results
            seed = int(hashlib.md5(user_id.encode()).hexdigest(), 16) % 100
            
            # Use the seed to generate performance metrics
            win_rate = 50 + (seed % 30)  # 50-80%
            profit_factor = 1.2 + (seed % 20) / 10  # 1.2-3.2
            
            performance = {
                "user_id": user_id,
                "total_signals": 100 + seed,
                "active_signals": 5 + (seed % 10),
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "avg_risk_reward": 2.5 + (seed % 15) / 10,
                "total_pips": 500 + seed * 10,
                "avg_holding_time": 12 + (seed % 24),  # hours
                "favorite_symbols": [
                    sample_symbols[seed % len(sample_symbols)],
                    sample_symbols[(seed + 1) % len(sample_symbols)],
                    sample_symbols[(seed + 2) % len(sample_symbols)]
                ],
                "favorite_timeframes": [
                    sample_timeframes[seed % len(sample_timeframes)],
                    sample_timeframes[(seed + 1) % len(sample_timeframes)]
                ]
            }
            
            logger.info(f"Retrieved performance for user {user_id}")
            return performance
            
        except Exception as e:
            logger.error(f"Error getting user performance: {str(e)}")
            return {}
    
    def get_signal_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get statistics about community signals.
        
        Args:
            days: Number of days to include in statistics
            
        Returns:
            Dictionary with signal statistics
        """
        try:
            # In a real implementation, this would make an API call
            # Simulate API response with sample data
            
            statistics = {
                "time_period": f"Last {days} days",
                "total_signals": 1200,
                "active_signals": 150,
                "executed_signals": 950,
                "expired_signals": 100,
                "win_rate": 65.5,
                "avg_profit_pct": 2.8,
                "avg_loss_pct": -1.2,
                "avg_risk_reward": 2.3,
                "popular_symbols": [
                    {"symbol": "ES", "count": 250},
                    {"symbol": "NQ", "count": 180},
                    {"symbol": "EURUSD", "count": 150},
                    {"symbol": "AAPL", "count": 120},
                    {"symbol": "GC", "count": 100}
                ],
                "popular_timeframes": [
                    {"timeframe": "1h", "count": 350},
                    {"timeframe": "4h", "count": 280},
                    {"timeframe": "1d", "count": 220},
                    {"timeframe": "15m", "count": 180},
                    {"timeframe": "5m", "count": 120}
                ]
            }
            
            logger.info(f"Retrieved signal statistics for last {days} days")
            return statistics
            
        except Exception as e:
            logger.error(f"Error getting signal statistics: {str(e)}")
            return {}
    
    def export_signals_to_csv(self, signals: List[TradingSignal], filepath: str) -> bool:
        """
        Export signals to a CSV file.
        
        Args:
            signals: List of signals to export
            filepath: Path to save CSV file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert signals to dictionaries
            data = [signal.to_dict() for signal in signals]
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Save to CSV
            df.to_csv(filepath, index=False)
            
            logger.info(f"Exported {len(signals)} signals to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting signals to CSV: {str(e)}")
            return False
    
    def get_signal_notifications(self, last_check: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get notifications about new signals from subscribed users.
        
        Args:
            last_check: Timestamp of last check
            
        Returns:
            List of notification dictionaries
        """
        if not self.subscribed_users:
            return []
        
        if last_check is None:
            # Default to 24 hours ago
            last_check = datetime.now() - timedelta(hours=24)
        
        try:
            # Get signals from subscribed users
            signals = self.get_subscribed_signals(active_only=False)
            
            # Filter for signals created after last check
            new_signals = [s for s in signals if s.created_at > last_check]
            
            # Convert to notification format
            notifications = []
            for signal in new_signals:
                notification = {
                    "type": "new_signal",
                    "signal_id": signal.signal_id,
                    "user_id": signal.user_id,
                    "username": signal.username,
                    "symbol": signal.symbol,
                    "direction": signal.direction,
                    "timeframe": signal.timeframe,
                    "created_at": signal.created_at.isoformat() if isinstance(signal.created_at, datetime) else signal.created_at,
                    "description": signal.description
                }
                notifications.append(notification)
            
            logger.info(f"Retrieved {len(notifications)} signal notifications")
            return notifications
            
        except Exception as e:
            logger.error(f"Error getting signal notifications: {str(e)}")
            return []
