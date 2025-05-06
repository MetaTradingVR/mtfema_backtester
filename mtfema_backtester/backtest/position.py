"""
Position class for tracking trades in the backtesting engine.
"""

from datetime import datetime
import uuid

class Position:
    """
    Represents a trading position (open or closed)
    
    This class maintains all the information about a single position
    including entry/exit details, profit/loss, and risk management parameters.
    """
    
    def __init__(
        self,
        symbol,
        direction,
        entry_price,
        size,
        entry_time=None,
        stop_loss=None,
        take_profit=None,
        timeframe=None,
        id=None
    ):
        """
        Initialize a new position
        
        Parameters:
        -----------
        symbol : str
            Trading symbol
        direction : str
            'long' or 'short'
        entry_price : float
            Entry price
        size : float
            Position size in shares/contracts
        entry_time : datetime or str, optional
            Entry time
        stop_loss : float, optional
            Stop loss price
        take_profit : float, optional
            Take profit price
        timeframe : str, optional
            Timeframe that generated the signal
        id : str, optional
            Unique identifier for the position
        """
        # Basic position details
        self.id = id if id else str(uuid.uuid4())
        self.symbol = symbol
        self.direction = direction.lower()
        self.entry_price = entry_price
        self.size = size
        self.entry_time = entry_time if entry_time else datetime.now()
        
        # Risk management
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.trailing_activated = False
        
        # Timeframe tracking
        self.timeframe = timeframe
        self.target_timeframe = timeframe
        
        # Exit details (initialize as None for open positions)
        self.exit_price = None
        self.exit_time = None
        self.exit_reason = None
        
        # Performance tracking
        self.realized_pnl = 0.0
        self.status = "open"
    
    def close(self, exit_price, exit_time=None, exit_reason=None):
        """
        Close the position
        
        Parameters:
        -----------
        exit_price : float
            Exit price
        exit_time : datetime or str, optional
            Exit time
        exit_reason : str, optional
            Reason for closing the position
            
        Returns:
        --------
        float
            Realized profit/loss
        """
        if self.status == "closed":
            return self.realized_pnl
        
        # Update exit details
        self.exit_price = exit_price
        self.exit_time = exit_time if exit_time else datetime.now()
        self.exit_reason = exit_reason if exit_reason else "manual"
        
        # Calculate profit/loss
        if self.direction == "long":
            self.realized_pnl = (self.exit_price - self.entry_price) * self.size
        else:  # short
            self.realized_pnl = (self.entry_price - self.exit_price) * self.size
        
        # Mark as closed
        self.status = "closed"
        
        return self.realized_pnl
    
    def current_pnl(self, current_price):
        """
        Calculate current unrealized profit/loss
        
        Parameters:
        -----------
        current_price : float
            Current market price
            
        Returns:
        --------
        float
            Unrealized profit/loss
        """
        if self.status == "closed":
            return self.realized_pnl
        
        if self.direction == "long":
            return (current_price - self.entry_price) * self.size
        else:  # short
            return (self.entry_price - current_price) * self.size
    
    def current_r_multiple(self, current_price=None):
        """
        Calculate current R multiple (profit/loss in terms of initial risk)
        
        Parameters:
        -----------
        current_price : float, optional
            Current market price (not needed for closed positions)
            
        Returns:
        --------
        float
            Current R multiple
        """
        # For closed positions, use exit price
        if self.status == "closed":
            price = self.exit_price
        else:
            if current_price is None:
                raise ValueError("Current price required for open positions")
            price = current_price
        
        # Calculate initial risk
        if self.stop_loss is None:
            return 0.0  # Can't calculate R multiple without stop loss
        
        initial_risk = abs(self.entry_price - self.stop_loss)
        if initial_risk == 0:
            return 0.0  # Avoid division by zero
        
        # Calculate profit/loss
        if self.direction == "long":
            profit_loss = price - self.entry_price
        else:  # short
            profit_loss = self.entry_price - price
        
        # Return R multiple
        return profit_loss / initial_risk
    
    def duration(self):
        """
        Calculate position duration
        
        Returns:
        --------
        timedelta
            Position duration
        """
        if self.status == "closed" and self.exit_time:
            end_time = self.exit_time
        else:
            end_time = datetime.now()
        
        # Handle string timestamps
        if isinstance(self.entry_time, str):
            entry_time = datetime.fromisoformat(self.entry_time.replace('Z', '+00:00'))
        else:
            entry_time = self.entry_time
            
        if isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        return end_time - entry_time
    
    def risk_reward_ratio(self):
        """
        Calculate risk/reward ratio
        
        Returns:
        --------
        float
            Risk/reward ratio (reward to risk)
        """
        if self.stop_loss is None or self.take_profit is None:
            return 0.0
        
        risk = abs(self.entry_price - self.stop_loss)
        reward = abs(self.entry_price - self.take_profit)
        
        if risk == 0:
            return 0.0  # Avoid division by zero
            
        return reward / risk
    
    def __str__(self):
        """String representation of the position"""
        status_str = self.status.upper()
        direction_str = self.direction.upper()
        
        if self.status == "open":
            return (f"{status_str} {direction_str} {self.size} {self.symbol} @ {self.entry_price:.2f} "
                   f"[SL: {self.stop_loss:.2f}, TP: {self.take_profit:.2f}]")
        else:
            return (f"{status_str} {direction_str} {self.size} {self.symbol} @ {self.entry_price:.2f} -> {self.exit_price:.2f} "
                   f"P&L: {self.realized_pnl:.2f} ({self.exit_reason})")
    
    def to_dict(self):
        """Convert position to dictionary for serialization"""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "size": self.size,
            "entry_time": str(self.entry_time),
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "trailing_activated": self.trailing_activated,
            "timeframe": self.timeframe,
            "target_timeframe": self.target_timeframe,
            "exit_price": self.exit_price,
            "exit_time": str(self.exit_time) if self.exit_time else None,
            "exit_reason": self.exit_reason,
            "realized_pnl": self.realized_pnl,
            "status": self.status
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create position from dictionary"""
        position = cls(
            symbol=data["symbol"],
            direction=data["direction"],
            entry_price=data["entry_price"],
            size=data["size"],
            entry_time=data["entry_time"],
            stop_loss=data["stop_loss"],
            take_profit=data["take_profit"],
            timeframe=data["timeframe"],
            id=data["id"]
        )
        
        position.trailing_activated = data["trailing_activated"]
        position.target_timeframe = data["target_timeframe"]
        position.exit_price = data["exit_price"]
        position.exit_time = data["exit_time"]
        position.exit_reason = data["exit_reason"]
        position.realized_pnl = data["realized_pnl"]
        position.status = data["status"]
        
        return position 