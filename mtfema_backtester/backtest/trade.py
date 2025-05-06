"""
Trade class for storing completed trades in the backtesting engine.
"""

from datetime import datetime

class Trade:
    """
    Represents a completed trade for analysis and reporting
    
    A Trade is created from a closed Position, providing a simplified
    and immutable record for analysis and performance reporting.
    """
    
    def __init__(
        self,
        id,
        symbol,
        direction,
        entry_price,
        exit_price,
        size,
        entry_time,
        exit_time,
        profit,
        timeframe,
        stop_loss=None,
        take_profit=None,
        exit_reason=None,
        target_timeframe=None,
        metadata=None
    ):
        """
        Initialize a Trade record
        
        Parameters:
        -----------
        id : str
            Unique identifier for the trade
        symbol : str
            Trading symbol
        direction : str
            'long' or 'short'
        entry_price : float
            Entry price
        exit_price : float
            Exit price
        size : float
            Position size
        entry_time : datetime or str
            Entry time
        exit_time : datetime or str
            Exit time
        profit : float
            Realized profit/loss
        timeframe : str
            Timeframe that generated the signal
        stop_loss : float, optional
            Stop loss price
        take_profit : float, optional
            Take profit price
        exit_reason : str, optional
            Reason for exiting the trade
        target_timeframe : str, optional
            Target timeframe for the trade
        metadata : dict, optional
            Additional metadata about the trade
        """
        self.id = id
        self.symbol = symbol
        self.direction = direction
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.size = size
        self.entry_time = entry_time
        self.exit_time = exit_time
        self.profit = profit
        self.timeframe = timeframe
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.exit_reason = exit_reason if exit_reason else "unknown"
        self.target_timeframe = target_timeframe if target_timeframe else timeframe
        self.metadata = metadata if metadata else {}
        
        # Calculate additional metrics
        self._calculate_metrics()
    
    @classmethod
    def from_position(cls, position):
        """
        Create a Trade from a closed Position
        
        Parameters:
        -----------
        position : Position
            Closed position to convert to a trade
            
        Returns:
        --------
        Trade
            Trade record
        """
        if position.status != "closed":
            raise ValueError("Cannot create Trade from an open Position")
        
        return cls(
            id=position.id,
            symbol=position.symbol,
            direction=position.direction,
            entry_price=position.entry_price,
            exit_price=position.exit_price,
            size=position.size,
            entry_time=position.entry_time,
            exit_time=position.exit_time,
            profit=position.realized_pnl,
            timeframe=position.timeframe,
            stop_loss=position.stop_loss,
            take_profit=position.take_profit,
            exit_reason=position.exit_reason,
            target_timeframe=position.target_timeframe
        )
    
    def _calculate_metrics(self):
        """Calculate additional trade metrics"""
        # Calculate percentage return
        if self.entry_price > 0:
            self.percent_return = (self.profit / (self.entry_price * self.size)) * 100
        else:
            self.percent_return = 0.0
        
        # Calculate R multiple (if stop loss is defined)
        if self.stop_loss is not None:
            initial_risk = abs(self.entry_price - self.stop_loss)
            if initial_risk > 0:
                if self.direction == "long":
                    profit_points = self.exit_price - self.entry_price
                else:  # short
                    profit_points = self.entry_price - self.exit_price
                
                self.r_multiple = profit_points / initial_risk
            else:
                self.r_multiple = 0.0
        else:
            self.r_multiple = 0.0
        
        # Calculate risk/reward ratio
        if self.stop_loss is not None and self.take_profit is not None:
            risk = abs(self.entry_price - self.stop_loss)
            reward = abs(self.entry_price - self.take_profit)
            
            if risk > 0:
                self.risk_reward_ratio = reward / risk
            else:
                self.risk_reward_ratio = 0.0
        else:
            self.risk_reward_ratio = 0.0
        
        # Calculate duration
        try:
            if isinstance(self.entry_time, str):
                entry_time = datetime.fromisoformat(self.entry_time.replace('Z', '+00:00'))
            else:
                entry_time = self.entry_time
                
            if isinstance(self.exit_time, str):
                exit_time = datetime.fromisoformat(self.exit_time.replace('Z', '+00:00'))
            else:
                exit_time = self.exit_time
                
            self.duration = exit_time - entry_time
            self.duration_hours = self.duration.total_seconds() / 3600
        except (ValueError, TypeError):
            self.duration = None
            self.duration_hours = 0.0
    
    def is_winner(self):
        """
        Check if the trade was profitable
        
        Returns:
        --------
        bool
            True if profitable, False otherwise
        """
        return self.profit > 0
    
    def __str__(self):
        """String representation of the trade"""
        direction_str = self.direction.upper()
        result = "WIN" if self.profit > 0 else "LOSS"
        
        return (f"{result} {direction_str} {self.size} {self.symbol} "
                f"@ {self.entry_price:.2f} -> {self.exit_price:.2f} "
                f"P&L: {self.profit:.2f} ({self.percent_return:.2f}%) "
                f"R: {self.r_multiple:.2f}")
    
    def to_dict(self):
        """Convert trade to dictionary for serialization"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "size": self.size,
            "entry_time": str(self.entry_time),
            "exit_time": str(self.exit_time),
            "profit": self.profit,
            "timeframe": self.timeframe,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "exit_reason": self.exit_reason,
            "target_timeframe": self.target_timeframe,
            "metadata": self.metadata,
            "percent_return": self.percent_return,
            "r_multiple": self.r_multiple,
            "risk_reward_ratio": self.risk_reward_ratio,
            "duration_hours": self.duration_hours
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create trade from dictionary"""
        trade = cls(
            id=data["id"],
            symbol=data["symbol"],
            direction=data["direction"],
            entry_price=data["entry_price"],
            exit_price=data["exit_price"],
            size=data["size"],
            entry_time=data["entry_time"],
            exit_time=data["exit_time"],
            profit=data["profit"],
            timeframe=data["timeframe"],
            stop_loss=data["stop_loss"],
            take_profit=data["take_profit"],
            exit_reason=data["exit_reason"],
            target_timeframe=data["target_timeframe"],
            metadata=data["metadata"]
        )
        
        # Add any additional calculated properties that were saved
        if "percent_return" in data:
            trade.percent_return = data["percent_return"]
        if "r_multiple" in data:
            trade.r_multiple = data["r_multiple"]
        if "risk_reward_ratio" in data:
            trade.risk_reward_ratio = data["risk_reward_ratio"]
        if "duration_hours" in data:
            trade.duration_hours = data["duration_hours"]
        
        return trade 