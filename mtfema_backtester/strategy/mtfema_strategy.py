    def _update_higher_tf_bias(self, data: Dict[str, Dict]):
        """
        Update bias from higher timeframes.
        
        Args:
            data: Dictionary of current data rows keyed by timeframe
        """
        # Reset higher timeframe bias
        self.higher_tf_bias = {}
        
        # Process from higher to lower timeframes
        sorted_timeframes = sorted(
            self.timeframes, 
            key=lambda x: get_timeframe_minutes(x), 
            reverse=True
        )
        
        for tf in sorted_timeframes:
            if tf not in data:
                continue
                
            # Skip if indicators haven't been initialized
            if tf not in self.indicators:
                continue
                
            # Get current price and EMA
            close = data[tf]['close']
            ema = self.indicators[tf]['ema']
            
            if ema is None or len(ema) < 1:
                continue
                
            # Get current EMA value
            curr_ema = ema[-1]
            
            # Determine bias based on price relative to EMA
            if close > curr_ema:
                bias = "BULLISH"
            elif close < curr_ema:
                bias = "BEARISH"
            else:
                bias = "NEUTRAL"
                
            # Store the bias
            self.higher_tf_bias[tf] = bias
    
    def _has_recent_reclamation(self, timeframe: str) -> bool:
        """
        Check if there's a recent reclamation in the timeframe.
        
        Args:
            timeframe: Timeframe to check
            
        Returns:
            True if there's a recent unprocessed reclamation
        """
        if timeframe not in self.reclamations:
            return False
            
        reclamation = self.reclamations[timeframe]
        
        return not reclamation.get('processed', True)
    
    def _is_valid_signal_reclamation(self, timeframe: str, reclamation: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """
        Check if a reclamation is valid for signal generation.
        
        Args:
            timeframe: Timeframe of the reclamation
            reclamation: Reclamation dictionary
            data: Current market data
            
        Returns:
            True if reclamation is valid for a signal
        """
        # Check reclamation strength
        if reclamation['strength'] < self.reclamation_threshold:
            return False
        
        # Check for volume confirmation if required
        if self.use_volume_confirmation:
            # Skip if no volume data available
            if 'volume' not in data:
                logger.warning(f"Volume confirmation required but no volume data available for {timeframe}")
                return False
                
            # Example volume confirmation logic
            # This should be customized based on specific volume confirmation rules
            volume = data['volume']
            avg_volume = self.indicators.get(timeframe, {}).get('avg_volume')
            
            if avg_volume is not None and volume < avg_volume:
                return False
        
        # Mark reclamation as processed to avoid duplicate signals
        reclamation['processed'] = True
        
        # Increment valid pullbacks metric
        self.monitor.increment_metric('valid_pullbacks')
        
        return True
    
    def _check_higher_tf_alignment(self, timeframe: str, direction: str) -> bool:
        """
        Check if higher timeframes have aligned bias.
        
        Args:
            timeframe: Current timeframe
            direction: Signal direction (LONG/SHORT)
            
        Returns:
            True if higher timeframes have aligned bias
        """
        # Get all higher timeframes
        higher_tfs = self._get_higher_timeframes(timeframe)
        
        if not higher_tfs:
            # No higher timeframes to check
            return True
        
        # Check bias of higher timeframes
        aligned = True
        for tf in higher_tfs:
            if tf not in self.higher_tf_bias:
                continue
                
            bias = self.higher_tf_bias[tf]
            
            if direction == "LONG" and bias == "BEARISH":
                aligned = False
                break
            elif direction == "SHORT" and bias == "BULLISH":
                aligned = False
                break
        
        return aligned
    
    def _get_higher_timeframes(self, timeframe: str) -> List[str]:
        """
        Get all timeframes higher than the current one.
        
        Args:
            timeframe: Current timeframe
            
        Returns:
            List of higher timeframes
        """
        # Sort timeframes by minutes
        sorted_tfs = sorted(
            self.timeframes,
            key=lambda x: get_timeframe_minutes(x)
        )
        
        # Find index of current timeframe
        try:
            current_idx = sorted_tfs.index(timeframe)
        except ValueError:
            return []
        
        # Return all higher timeframes
        return sorted_tfs[current_idx+1:]
    
    def _calculate_exit_levels(self, timeframe: str, direction: str, entry_price: float,
                               atr_value: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate stop loss and take profit prices.
        
        Args:
            timeframe: Current timeframe
            direction: Trade direction (LONG/SHORT)
            entry_price: Entry price
            atr_value: Current ATR value
            
        Returns:
            Tuple of (stop_loss_price, take_profit_price)
        """
        # Get ATR multipliers from trade management
        sl_multiple = self.trade_management.get('stop_loss_atr_multiple', 1.5)
        tp_multiple = self.trade_management.get('take_profit_atr_multiple', 3.0)
        
        # If no ATR value is available, use a percentage of price
        if atr_value is None or atr_value <= 0:
            logger.warning(f"No valid ATR value available for {timeframe}, using percentage-based exits")
            
            # Default to 1.5% for stop loss and 3% for take profit
            sl_percentage = 0.015
            tp_percentage = 0.03
            
            if direction == "LONG":
                stop_loss = entry_price * (1 - sl_percentage)
                take_profit = entry_price * (1 + tp_percentage)
            else:  # SHORT
                stop_loss = entry_price * (1 + sl_percentage)
                take_profit = entry_price * (1 - tp_percentage)
                
            return stop_loss, take_profit
        
        # Calculate stop loss and take profit based on ATR
        if direction == "LONG":
            stop_loss = entry_price - (atr_value * sl_multiple)
            take_profit = entry_price + (atr_value * tp_multiple)
        else:  # SHORT
            stop_loss = entry_price + (atr_value * sl_multiple)
            take_profit = entry_price - (atr_value * tp_multiple)
        
        return stop_loss, take_profit
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate Exponential Moving Average.
        
        Args:
            prices: Array of prices
            period: EMA period
            
        Returns:
            Array of EMA values
        """
        if len(prices) < period:
            return None
            
        # Convert to numpy array if it's not already
        prices = np.array(prices)
        
        # Calculate EMA
        ema = np.zeros_like(prices)
        
        # Initialize with SMA
        ema[:period] = np.mean(prices[:period])
        
        # Calculate EMA for the rest of the values
        alpha = 2 / (period + 1)
        for i in range(period, len(prices)):
            ema[i] = prices[i] * alpha + ema[i-1] * (1 - alpha)
        
        return ema
    
    def _calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate Average True Range.
        
        Args:
            high: Array of high prices
            low: Array of low prices
            close: Array of close prices
            period: ATR period
            
        Returns:
            Array of ATR values
        """
        if len(high) < period + 1 or len(low) < period + 1 or len(close) < period + 1:
            return None
            
        # Convert to numpy arrays if they're not already
        high = np.array(high)
        low = np.array(low)
        close = np.array(close)
        
        # Calculate true range
        tr = np.zeros(len(high))
        
        # First value is just high - low
        tr[0] = high[0] - low[0]
        
        # Calculate true range for the rest
        for i in range(1, len(high)):
            tr1 = high[i] - low[i]
            tr2 = abs(high[i] - close[i-1])
            tr3 = abs(low[i] - close[i-1])
            tr[i] = max(tr1, tr2, tr3)
        
        # Calculate ATR
        atr = np.zeros_like(tr)
        
        # Initialize with SMA of TR
        atr[:period] = np.mean(tr[:period])
        
        # Calculate smoothed ATR
        for i in range(period, len(tr)):
            atr[i] = (atr[i-1] * (period - 1) + tr[i]) / period
        
        return atr
    
    def _calculate_extensions(self, prices: np.ndarray, ema: np.ndarray, atr: np.ndarray) -> np.ndarray:
        """
        Calculate price extensions from EMA.
        
        Args:
            prices: Array of price values
            ema: Array of EMA values
            atr: Array of ATR values
            
        Returns:
            Array of extension values (in ATR units)
        """
        if ema is None or atr is None:
            return None
            
        if len(prices) != len(ema) or len(prices) != len(atr):
            logger.warning("Price, EMA, and ATR arrays must be the same length")
            return None
            
        # Calculate extensions in ATR units
        extensions = np.abs(prices - ema) / atr
        
        return extensions
