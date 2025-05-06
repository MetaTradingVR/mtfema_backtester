            # Check for short setup
            short_signal = (
                trend_bearish and  # Primary timeframe is bearish
                entry_distance > self.extension_threshold and  # Price extended above EMA on entry TF
                entry_distance < entry_distance_prev  # Price starting to revert back toward EMA
            )
            
            # Generate signals based on setups
            current_price = entry_df['close'].iloc[-1]
            
            if long_signal:
                # Calculate stop loss and take profit levels
                stop_loss = current_price * (1 - self.stop_loss_pct / 100)
                take_profit = current_price * (1 + self.profit_target_pct / 100)
                
                # Create long signal
                signal = {
                    'symbol': symbol,
                    'direction': 'buy',
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'date': current_date,
                    'timeframe': self.entry_tf,
                    'primary_trend': 'bullish',
                    'ema_distance': entry_distance,
                    'risk_reward': self.profit_target_pct / self.stop_loss_pct
                }
                
                signals.append(signal)
                
            elif short_signal:
                # Calculate stop loss and take profit levels
                stop_loss = current_price * (1 + self.stop_loss_pct / 100)
                take_profit = current_price * (1 - self.profit_target_pct / 100)
                
                # Create short signal
                signal = {
                    'symbol': symbol,
                    'direction': 'sell',
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'date': current_date,
                    'timeframe': self.entry_tf,
                    'primary_trend': 'bearish',
                    'ema_distance': entry_distance,
                    'risk_reward': self.profit_target_pct / self.stop_loss_pct
                }
                
                signals.append(signal)
        
        return signals
    
    def update_trades(self, data: Dict[str, Dict[str, pd.DataFrame]], current_date: datetime) -> List[Dict[str, Any]]:
        """
        Update active trades based on current market data.
        
        Args:
            data: Dictionary of DataFrames for different symbols and timeframes
            current_date: Current date in the backtest
            
        Returns:
            List of closed trade dictionaries
        """
        closed_trades = []
        
        for symbol, trades in self.active_trades.items():
            # Skip if no active trades for this symbol
            if not trades:
                continue
            
            # Skip if symbol data is missing
            if symbol not in data or self.entry_tf not in data[symbol]:
                continue
            
            # Get latest price data
            df = data[symbol][self.entry_tf]
            current_high = df['high'].iloc[-1]
            current_low = df['low'].iloc[-1]
            current_close = df['close'].iloc[-1]
            
            # Check each active trade
            remaining_trades = []
            
            for trade in trades:
                # Check if stop loss hit
                if trade['direction'] == 'buy' and current_low <= trade['stop_loss']:
                    # Long position stopped out
                    trade['exit_price'] = trade['stop_loss']
                    trade['exit_date'] = current_date
                    trade['exit_reason'] = 'stop_loss'
                    trade['profit_pct'] = (trade['exit_price'] / trade['entry_price'] - 1) * 100
                    
                    closed_trades.append(trade)
                
                elif trade['direction'] == 'sell' and current_high >= trade['stop_loss']:
                    # Short position stopped out
                    trade['exit_price'] = trade['stop_loss']
                    trade['exit_date'] = current_date
                    trade['exit_reason'] = 'stop_loss'
                    trade['profit_pct'] = (1 - trade['exit_price'] / trade['entry_price']) * 100
                    
                    closed_trades.append(trade)
                
                # Check if take profit hit
                elif trade['direction'] == 'buy' and current_high >= trade['take_profit']:
                    # Long position take profit hit
                    trade['exit_price'] = trade['take_profit']
                    trade['exit_date'] = current_date
                    trade['exit_reason'] = 'take_profit'
                    trade['profit_pct'] = (trade['exit_price'] / trade['entry_price'] - 1) * 100
                    
                    closed_trades.append(trade)
                
                elif trade['direction'] == 'sell' and current_low <= trade['take_profit']:
                    # Short position take profit hit
                    trade['exit_price'] = trade['take_profit']
                    trade['exit_date'] = current_date
                    trade['exit_reason'] = 'take_profit'
                    trade['profit_pct'] = (1 - trade['exit_price'] / trade['entry_price']) * 100
                    
                    closed_trades.append(trade)
                
                else:
                    # Trade still active
                    remaining_trades.append(trade)
            
            # Update active trades for this symbol
            self.active_trades[symbol] = remaining_trades
        
        return closed_trades
    
    def on_new_signal(self, signal: Dict[str, Any]):
        """
        Process a new trading signal.
        
        Args:
            signal: Signal dictionary with trade details
        """
        symbol = signal['symbol']
        
        # Add to active trades
        self.active_trades[symbol].append(signal)
    
    def on_trade_closed(self, trade: Dict[str, Any]):
        """
        Process a closed trade.
        
        Args:
            trade: Closed trade dictionary
        """
        # This method can be overridden to perform custom actions when a trade is closed
        pass
    
    def get_position_size(self, signal: Dict[str, Any], account_balance: float, risk_percent: float = 1.0) -> float:
        """
        Calculate position size based on risk management.
        
        Args:
            signal: Signal dictionary with trade details
            account_balance: Current account balance
            risk_percent: Percentage of account balance to risk per trade
            
        Returns:
            Position size in units
        """
        # Calculate risk amount
        risk_amount = account_balance * (risk_percent / 100)
        
        # Calculate dollar risk per unit
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        
        if signal['direction'] == 'buy':
            dollar_risk_per_unit = entry_price - stop_loss
        else:
            dollar_risk_per_unit = stop_loss - entry_price
        
        # Calculate position size
        if dollar_risk_per_unit <= 0:
            return 0
        
        position_size = risk_amount / dollar_risk_per_unit
        
        # Round to appropriate precision
        position_size = round(position_size, 2)
        
        return position_size
    
    def generate_entry_orders(self, signal: Dict[str, Any], account_balance: float) -> Dict[str, Any]:
        """
        Generate order details for a signal.
        
        Args:
            signal: Signal dictionary with trade details
            account_balance: Current account balance
            
        Returns:
            Order details dictionary
        """
        # Calculate position size
        position_size = self.get_position_size(signal, account_balance)
        
        # Create order details
        order = {
            'symbol': signal['symbol'],
            'direction': signal['direction'],
            'order_type': 'market',
            'quantity': position_size,
            'price': signal['entry_price'],
            'stop_loss': signal['stop_loss'],
            'take_profit': signal['take_profit'],
            'signal_date': signal['date'],
            'signal_details': {
                'timeframe': signal['timeframe'],
                'primary_trend': signal['primary_trend'],
                'ema_distance': signal['ema_distance'],
                'risk_reward': signal['risk_reward']
            }
        }
        
        return order
    
    def adjust_for_market_conditions(self, signals: List[Dict[str, Any]], 
                                     data: Dict[str, Dict[str, pd.DataFrame]], 
                                     market_regime: str = 'normal') -> List[Dict[str, Any]]:
        """
        Adjust signals based on current market conditions and regime.
        
        Args:
            signals: List of signal dictionaries
            data: Dictionary of DataFrames for different symbols and timeframes
            market_regime: Current market regime ('trending', 'ranging', 'volatile', 'normal')
            
        Returns:
            Adjusted list of signals
        """
        # Filter or adjust signals based on market regime
        if not signals:
            return signals
        
        filtered_signals = []
        
        for signal in signals:
            symbol = signal['symbol']
            
            # Skip if necessary data is missing
            if symbol not in data or self.primary_tf not in data[symbol]:
                continue
            
            # Get primary timeframe data
            df = data[symbol][self.primary_tf]
            
            # Calculate volatility (standard deviation of returns)
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * 100  # Convert to percentage
            
            # Adjust signal based on market regime
            if market_regime == 'volatile' and volatility > 2.0:
                # In volatile markets, only take high-probability setups with good risk/reward
                if signal['risk_reward'] >= 2.0 and abs(signal['ema_distance']) > 1.0:
                    filtered_signals.append(signal)
            
            elif market_regime == 'ranging':
                # In ranging markets, take more mean-reversion trades (larger extensions)
                if abs(signal['ema_distance']) > 1.5:
                    filtered_signals.append(signal)
            
            elif market_regime == 'trending':
                # In trending markets, favor trades in the direction of the primary trend
                primary_ema = df['ema'].iloc[-1]
                primary_close = df['close'].iloc[-1]
                
                if (signal['direction'] == 'buy' and primary_close > primary_ema) or \
                   (signal['direction'] == 'sell' and primary_close < primary_ema):
                    filtered_signals.append(signal)
            
            else:
                # Normal market conditions, no special filtering
                filtered_signals.append(signal)
        
        return filtered_signals
