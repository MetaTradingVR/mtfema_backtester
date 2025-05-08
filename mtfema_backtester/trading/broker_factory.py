"""
Broker Factory for the MT 9 EMA Extension Strategy.

This module provides a factory for creating broker implementations.
"""

import logging
from typing import Dict, Any, Type, List, Optional

from .broker_interface import BrokerInterface
from .tradovate_broker import TradovateBroker
from .rithmic_broker import RithmicBroker

logger = logging.getLogger(__name__)

class BrokerFactory:
    """
    Factory for creating broker instances.
    
    Provides a central registry for available broker implementations
    and methods for creating new broker instances.
    """
    
    # Registry of available broker implementations
    _broker_registry: Dict[str, Type[BrokerInterface]] = {}
    
    @classmethod
    def register(cls, broker_name: str, broker_class: Type[BrokerInterface]):
        """
        Register a broker implementation.
        
        Args:
            broker_name: Name of the broker
            broker_class: Broker class
        """
        cls._broker_registry[broker_name.lower()] = broker_class
        logger.info(f"Registered broker implementation: {broker_name}")
    
    @classmethod
    def create(cls, 
               broker_name: str, 
               credentials: Dict[str, Any], 
               is_paper: bool = True) -> BrokerInterface:
        """
        Create a broker instance.
        
        Args:
            broker_name: Name of the broker
            credentials: Broker credentials
            is_paper: Whether to use paper trading
            
        Returns:
            BrokerInterface: Broker instance
            
        Raises:
            ValueError: If broker not found
        """
        broker_key = broker_name.lower()
        
        # Register default brokers if not already registered
        if not cls._broker_registry:
            cls._register_default_brokers()
            
        if broker_key not in cls._broker_registry:
            available = ', '.join(cls._broker_registry.keys())
            raise ValueError(f"Broker '{broker_name}' not found. Available brokers: {available}")
        
        # Create instance
        broker_class = cls._broker_registry[broker_key]
        
        logger.info(f"Creating broker instance for: {broker_name} (Paper: {is_paper})")
        return broker_class(credentials=credentials, is_paper=is_paper)
    
    @classmethod
    def get_available_brokers(cls) -> List[str]:
        """
        Get list of available brokers.
        
        Returns:
            List[str]: Available broker names
        """
        # Register default brokers if not already registered
        if not cls._broker_registry:
            cls._register_default_brokers()
            
        return list(cls._broker_registry.keys())
    
    @classmethod
    def _register_default_brokers(cls):
        """Register default broker implementations."""
        cls.register("tradovate", TradovateBroker)
        cls.register("rithmic", RithmicBroker)

# Register default brokers when module is imported
BrokerFactory._register_default_brokers()
