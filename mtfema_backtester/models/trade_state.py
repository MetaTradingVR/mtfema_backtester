"""
Progressive Trade State Management for MT 9 EMA Backtester.

This module provides a state machine approach to trade management,
tracking trade progression through the timeframe hierarchy with
clearly defined state transitions and actions.
"""

from enum import Enum
from typing import Dict, List, Any, Optional, Union, Callable
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TradeState(Enum):
    """
    Enumeration of possible trade states in the progressive targeting framework.
    """
    PENDING = "pending"         # Signal generated but not yet executed
    ACTIVE = "active"           # Position is open
    TARGET1 = "target1"         # First target hit
    TARGET2 = "target2"         # Second target hit
    TARGET3 = "target3"         # Third target hit
    TARGET4 = "target4"         # Fourth target hit
    STOPPED = "stopped"         # Stopped out
    COMPLETED = "completed"     # Successfully completed all targets
    CANCELED = "canceled"       # Signal canceled before execution
    EXPIRED = "expired"         # Signal expired before execution
    
    def __str__(self):
        return self.value


class TradeTransition:
    """
    Represents a state transition in the trade lifecycle.
    """
    def __init__(self, 
                 from_state: TradeState, 
                 to_state: TradeState, 
                 timestamp: datetime,
                 reason: str,
                 details: Dict[str, Any] = None):
        """
        Initialize a trade transition.
        
        Args:
            from_state: State before transition
            to_state: State after transition
            timestamp: When the transition occurred
            reason: Reason for the transition
            details: Additional transition details
        """
        self.from_state = from_state
        self.to_state = to_state
        self.timestamp = timestamp
        self.reason = reason
        self.details = details or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the transition
        """
        return {
            "from_state": str(self.from_state),
            "to_state": str(self.to_state),
            "timestamp": self.timestamp.isoformat(),
            "reason": self.reason,
            "details": self.details
        }


class ProgressiveTradeManager:
    """
    Manages trade progression through the timeframe hierarchy 
    using a state machine approach.
    """
    
    def __init__(self):
        """
        Initialize the trade manager.
        """
        # Define valid state transitions
        self.valid_transitions = {
            # From pending to active or canceled
            TradeState.PENDING: [
                TradeState.ACTIVE,
                TradeState.CANCELED,
                TradeState.EXPIRED
            ],
            
            # From active to first target, stopped, or completed
            TradeState.ACTIVE: [
                TradeState.TARGET1,
                TradeState.STOPPED,
                TradeState.COMPLETED
            ],
            
            # From first target to second target, stopped, or completed
            TradeState.TARGET1: [
                TradeState.TARGET2,
                TradeState.STOPPED,
                TradeState.COMPLETED
            ],
            
            # From second target to third target, stopped, or completed
            TradeState.TARGET2: [
                TradeState.TARGET3,
                TradeState.STOPPED,
                TradeState.COMPLETED
            ],
            
            # From third target to fourth target, stopped, or completed
            TradeState.TARGET3: [
                TradeState.TARGET4,
                TradeState.STOPPED,
                TradeState.COMPLETED
            ],
            
            # From fourth target to stopped or completed
            TradeState.TARGET4: [
                TradeState.STOPPED,
                TradeState.COMPLETED
            ],
            
            # Terminal states - no transitions out
            TradeState.STOPPED: [],
            TradeState.COMPLETED: [],
            TradeState.CANCELED: [],
            TradeState.EXPIRED: []
        }
        
        # Actions to take on state transitions
        self.transition_actions = {}
        
        # Register default transition actions
        self._register_default_actions()
        
        logger.info("Progressive trade manager initialized")
    
    def _register_default_actions(self) -> None:
        """
        Register default actions for state transitions.
        """
        # Transition from PENDING to ACTIVE
        self.register_transition_action(
            TradeState.PENDING,
            TradeState.ACTIVE,
            self._on_trade_activation
        )
        
        # Transition from ACTIVE to TARGET1
        self.register_transition_action(
            TradeState.ACTIVE,
            TradeState.TARGET1,
            self._on_target1_hit
        )
        
        # Transition from TARGET1 to TARGET2
        self.register_transition_action(
            TradeState.TARGET1,
            TradeState.TARGET2,
            self._on_target2_hit
        )
        
        # Transition from any state to STOPPED
        for state in [TradeState.ACTIVE, TradeState.TARGET1, 
                     TradeState.TARGET2, TradeState.TARGET3]:
            self.register_transition_action(
                state,
                TradeState.STOPPED,
                self._on_stop_triggered
            )
    
    def register_transition_action(self, 
                                  from_state: TradeState, 
                                  to_state: TradeState, 
                                  action: Callable[[Dict[str, Any], Dict[str, Any]], None]) -> None:
        """
        Register an action to be executed on a state transition.
        
        Args:
            from_state: State before transition
            to_state: State after transition
            action: Function to call with (position, transition_details)
        """
        key = (from_state, to_state)
        self.transition_actions[key] = action
        
        logger.debug(f"Registered action for transition {from_state} -> {to_state}")
    
    def transition_state(self, 
                        position: Dict[str, Any], 
                        to_state: TradeState, 
                        reason: str, 
                        details: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Transition a position to a new state.
        
        Args:
            position: Position dictionary
            to_state: New state
            reason: Reason for the transition
            details: Additional transition details
            
        Returns:
            Updated position dictionary
            
        Raises:
            ValueError: If the transition is invalid
        """
        # Get current state
        current_state = TradeState(position.get('state', 'pending'))
        
        # Check if transition is valid
        if to_state not in self.valid_transitions[current_state]:
            raise ValueError(f"Invalid state transition: {current_state} -> {to_state}")
        
        # Create transition record
        transition = TradeTransition(
            from_state=current_state,
            to_state=to_state,
            timestamp=datetime.now(),
            reason=reason,
            details=details or {}
        )
        
        # Initialize state history if not present
        if 'state_history' not in position:
            position['state_history'] = []
        
        # Add transition to history
        position['state_history'].append(transition.to_dict())
        
        # Update current state
        position['state'] = str(to_state)
        position['state_changed_at'] = transition.timestamp.isoformat()
        
        # Execute transition action if registered
        action_key = (current_state, to_state)
        if action_key in self.transition_actions:
            self.transition_actions[action_key](position, details or {})
        
        logger.info(f"Position transitioned from {current_state} to {to_state}: {reason}")
        
        return position
    
    def get_valid_next_states(self, position: Dict[str, Any]) -> List[TradeState]:
        """
        Get valid next states for a position.
        
        Args:
            position: Position dictionary
            
        Returns:
            List of valid next states
        """
        current_state = TradeState(position.get('state', 'pending'))
        return self.valid_transitions[current_state]
    
    def is_terminal_state(self, position: Dict[str, Any]) -> bool:
        """
        Check if a position is in a terminal state.
        
        Args:
            position: Position dictionary
            
        Returns:
            Whether the position is in a terminal state
        """
        current_state = TradeState(position.get('state', 'pending'))
        return len(self.valid_transitions[current_state]) == 0
    
    def _on_trade_activation(self, position: Dict[str, Any], details: Dict[str, Any]) -> None:
        """
        Action to take when a trade is activated.
        
        Args:
            position: Position dictionary
            details: Transition details
        """
        # Record entry details
        position['entry_time'] = details.get('time', datetime.now().isoformat())
        position['entry_price'] = details.get('price')
        position['entry_reason'] = details.get('reason', 'Signal execution')
        
        # Log the entry
        logger.info(f"Trade activated: {position['direction']} at {position['entry_price']}")
    
    def _on_target1_hit(self, position: Dict[str, Any], details: Dict[str, Any]) -> None:
        """
        Action to take when the first target is hit.
        
        Args:
            position: Position dictionary
            details: Transition details
        """
        # Move stop to breakeven
        position['stop_level'] = position['entry_price']
        
        # Record target details
        self._record_target_hit(position, 1, details)
        
        # Log the target hit
        logger.info(f"Target 1 hit: {position['direction']} at {details.get('price')}, stop moved to breakeven")
    
    def _on_target2_hit(self, position: Dict[str, Any], details: Dict[str, Any]) -> None:
        """
        Action to take when the second target is hit.
        
        Args:
            position: Position dictionary
            details: Transition details
        """
        # Move stop to first target
        target1_price = position.get('targets_hit', [])[0].get('price')
        if target1_price:
            position['stop_level'] = target1_price
        
        # Record target details
        self._record_target_hit(position, 2, details)
        
        # Log the target hit
        logger.info(f"Target 2 hit: {position['direction']} at {details.get('price')}, stop moved to target 1")
    
    def _on_stop_triggered(self, position: Dict[str, Any], details: Dict[str, Any]) -> None:
        """
        Action to take when a stop is triggered.
        
        Args:
            position: Position dictionary
            details: Transition details
        """
        # Record exit details
        position['exit_time'] = details.get('time', datetime.now().isoformat())
        position['exit_price'] = details.get('price')
        position['exit_reason'] = 'Stop triggered'
        
        # Calculate profit/loss
        if 'entry_price' in position and 'exit_price' in position:
            if position['direction'] == 'LONG':
                position['profit'] = position['exit_price'] - position['entry_price']
            else:
                position['profit'] = position['entry_price'] - position['exit_price']
            
            position['profit_pct'] = position['profit'] / position['entry_price'] * 100
        
        # Log the stop
        logger.info(f"Stop triggered: {position['direction']} at {position['exit_price']}, P&L: {position.get('profit_pct', 0):.2f}%")
    
    def _record_target_hit(self, position: Dict[str, Any], target_number: int, details: Dict[str, Any]) -> None:
        """
        Record a target hit in the position.
        
        Args:
            position: Position dictionary
            target_number: Target number (1, 2, 3, etc.)
            details: Target hit details
        """
        # Initialize targets_hit if not present
        if 'targets_hit' not in position:
            position['targets_hit'] = []
        
        # Create target hit record
        target_hit = {
            'target_number': target_number,
            'price': details.get('price'),
            'time': details.get('time', datetime.now().isoformat()),
            'timeframe': details.get('timeframe')
        }
        
        # Add to targets hit
        position['targets_hit'].append(target_hit)
        
        # Update position data
        if details.get('next_target'):
            position['current_target'] = details.get('next_target')
            position['target_timeframe'] = details.get('next_timeframe')


# Create a global instance for convenience
_trade_manager = ProgressiveTradeManager()

def get_trade_manager() -> ProgressiveTradeManager:
    """
    Get the global trade manager instance.
    
    Returns:
        ProgressiveTradeManager instance
    """
    return _trade_manager
