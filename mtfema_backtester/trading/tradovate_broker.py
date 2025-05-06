            timeframe_map = {
                "1m": {"chartDescription": "Min", "chartUnit": "m", "chartUnits": 1},
                "5m": {"chartDescription": "Min", "chartUnit": "m", "chartUnits": 5},
                "15m": {"chartDescription": "Min", "chartUnit": "m", "chartUnits": 15},
                "30m": {"chartDescription": "Min", "chartUnit": "m", "chartUnits": 30},
                "1h": {"chartDescription": "Hour", "chartUnit": "h", "chartUnits": 1},
                "4h": {"chartDescription": "Hour", "chartUnit": "h", "chartUnits": 4},
                "1d": {"chartDescription": "Day", "chartUnit": "d", "chartUnits": 1}
            }
            
            if timeframe not in timeframe_map:
                raise ValueError(f"Unsupported timeframe: {timeframe}")
            
            # Prepare chart request
            url = urljoin(self._base_url, "chart/get")
            
            headers = {
                "Authorization": f"Bearer {self._access_token}"
            }
            
            # Calculate underlyingType
            tf_settings = timeframe_map[timeframe]
            
            payload = {
                "contractId": contract_id,
                "chartDescription": tf_settings["chartDescription"],
                "underlyingType": "contract",
                "chartUnit": tf_settings["chartUnit"],
                "chartUnits": tf_settings["chartUnits"],
                "barsBack": count
            }
            
            # Get chart data
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            chart_data = response.json()
            bars = chart_data.get("bars", [])
            
            # Convert to DataFrame
            data = {
                "timestamp": [],
                "open": [],
                "high": [],
                "low": [],
                "close": [],
                "volume": []
            }
            
            for bar in bars:
                data["timestamp"].append(datetime.fromtimestamp(bar["timestamp"] / 1000))
                data["open"].append(bar["open"])
                data["high"].append(bar["high"])
                data["low"].append(bar["low"])
                data["close"].append(bar["close"])
                data["volume"].append(bar.get("volume", 0))
            
            df = pd.DataFrame(data)
            if not df.empty:
                df.set_index("timestamp", inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    
    def get_current_price(self, symbol: str) -> Dict[str, float]:
        """
        Get current market price for a symbol.
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Dictionary with price information (bid, ask, last)
        """
        if not self.is_connected:
            raise RuntimeError("Broker is not connected")
        
        # First check if we already have price data
        if symbol in self._current_prices:
            return self._current_prices[symbol]
        
        try:
            # Get contract ID for symbol
            contract_id = self._get_contract_id(symbol)
            if not contract_id:
                raise ValueError(f"Contract not found for symbol: {symbol}")
            
            # Request quote data
            url = urljoin(self._base_url, "md/getQuote")
            
            headers = {
                "Authorization": f"Bearer {self._md_access_token}"
            }
            
            params = {
                "contractId": contract_id
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            quote_data = response.json()
            
            # Extract price data
            bid = quote_data.get("bid", 0.0)
            ask = quote_data.get("ask", 0.0)
            last = quote_data.get("last", 0.0)
            
            # If missing last price, use mid price
            if last == 0.0 and bid > 0.0 and ask > 0.0:
                last = (bid + ask) / 2
            
            # Create price data
            price_data = {
                "bid": bid,
                "ask": ask,
                "last": last,
                "timestamp": datetime.now()
            }
            
            # Update current prices
            self._current_prices[symbol] = price_data
            
            return price_data
            
        except Exception as e:
            logger.error(f"Error getting current price: {str(e)}")
            
            # Return default values
            return {
                "bid": 0.0,
                "ask": 0.0,
                "last": 0.0,
                "timestamp": datetime.now()
            }
    
    def subscribe_to_market_data(self, symbol: str, callback: callable):
        """
        Subscribe to real-time market data.
        
        Args:
            symbol: Trading symbol
            callback: Function to call with market data updates
        """
        if not self.is_connected:
            raise RuntimeError("Broker is not connected")
        
        try:
            # Get contract ID for symbol
            contract_id = self._get_contract_id(symbol)
            if not contract_id:
                raise ValueError(f"Contract not found for symbol: {symbol}")
            
            # Initialize subscription list if needed
            if symbol not in self._subscriptions:
                self._subscriptions[symbol] = []
            
            # Add callback if not already subscribed
            if callback not in self._subscriptions[symbol]:
                self._subscriptions[symbol].append(callback)
            
            # Subscribe to market data via WebSocket
            if self._ws_connected:
                with self._ws_lock:
                    subscribe_msg = {
                        "command": "md-subscribe",
                        "payload": {
                            "Symbol": symbol,
                            "ContractId": contract_id
                        }
                    }
                    self._ws.send(json.dumps(subscribe_msg))
            
            logger.info(f"Subscribed to market data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error subscribing to market data: {str(e)}")
    
    def unsubscribe_from_market_data(self, symbol: str):
        """
        Unsubscribe from real-time market data.
        
        Args:
            symbol: Trading symbol
        """
        if not self.is_connected:
            return
        
        try:
            # Get contract ID for symbol
            contract_id = self._get_contract_id(symbol)
            if not contract_id:
                return
            
            # Remove all callbacks
            if symbol in self._subscriptions:
                del self._subscriptions[symbol]
            
            # Unsubscribe via WebSocket
            if self._ws_connected:
                with self._ws_lock:
                    unsubscribe_msg = {
                        "command": "md-unsubscribe",
                        "payload": {
                            "Symbol": symbol,
                            "ContractId": contract_id
                        }
                    }
                    self._ws.send(json.dumps(unsubscribe_msg))
            
            logger.info(f"Unsubscribed from market data for {symbol}")
            
        except Exception as e:
            logger.error(f"Error unsubscribing from market data: {str(e)}")
