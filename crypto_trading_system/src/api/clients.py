"""
API client for interacting with Coinbase and other cryptocurrency APIs.

This module provides clients for fetching cryptocurrency data from various sources.
"""

import os
import json
import time
import hmac
import hashlib
import base64
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from ..utils.helpers import setup_logging
from ..config.settings import COINBASE_API_KEY, COINBASE_API_SECRET, COINBASE_API_PASSPHRASE, DEMO_MODE

# Set up logging
logger = setup_logging("crypto_trading_system")

class CoinbaseClient:
    """Client for interacting with Coinbase Pro API."""
    
    def __init__(self, api_key: str = None, api_secret: str = None, api_passphrase: str = None, demo_mode: bool = None):
        """
        Initialize Coinbase client.
        
        Args:
            api_key: Coinbase API key
            api_secret: Coinbase API secret
            api_passphrase: Coinbase API passphrase
            demo_mode: Whether to use demo mode (overrides global setting)
        """
        self.api_key = api_key or COINBASE_API_KEY
        self.api_secret = api_secret or COINBASE_API_SECRET
        self.api_passphrase = api_passphrase or COINBASE_API_PASSPHRASE
        self.demo_mode = demo_mode if demo_mode is not None else (DEMO_MODE or not all([self.api_key, self.api_secret, self.api_passphrase]))
        
        self.base_url = "https://api.exchange.coinbase.com"
        
        if not self.api_key or not self.api_secret or not self.api_passphrase:
            logger.warning("Coinbase API credentials not provided. Some functionality will be limited.")
            self.demo_mode = True
    
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        """Generate signature for Coinbase API authentication."""
        message = timestamp + method + request_path + body
        signature = hmac.new(
            base64.b64decode(self.api_secret),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """
        Make authenticated request to Coinbase API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body
            
        Returns:
            API response
        """
        if self.demo_mode:
            logger.info(f"Demo mode: {method} {endpoint}")
            return self._get_demo_response(method, endpoint, params, data)
        
        url = f"{self.base_url}{endpoint}"
        
        timestamp = str(int(time.time()))
        body = json.dumps(data) if data else ""
        
        headers = {
            "CB-ACCESS-KEY": self.api_key,
            "CB-ACCESS-SIGN": self._generate_signature(timestamp, method, endpoint, body),
            "CB-ACCESS-TIMESTAMP": timestamp,
            "CB-ACCESS-PASSPHRASE": self.api_passphrase,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=body,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Coinbase API request error: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            return {"error": str(e)}
    
    def _get_demo_response(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict[str, Any]:
        """Generate demo responses for testing."""
        import random
        
        # Product endpoints
        if endpoint == "/products":
            return {
                "products": [
                    {
                        "product_id": "BTC-USD",
                        "price": f"{random.uniform(45000, 55000):.2f}",
                        "volume_24h": "12345.67",
                        "status": "online",
                        "quote_currency_id": "USD",
                        "base_currency_id": "BTC"
                    },
                    {
                        "product_id": "ETH-USD",
                        "price": f"{random.uniform(2800, 3200):.2f}",
                        "volume_24h": "54321.98",
                        "status": "online",
                        "quote_currency_id": "USD",
                        "base_currency_id": "ETH"
                    },
                    {
                        "product_id": "SOL-USD",
                        "price": f"{random.uniform(40, 50):.2f}",
                        "volume_24h": "98765.43",
                        "status": "online",
                        "quote_currency_id": "USD",
                        "base_currency_id": "SOL"
                    }
                ]
            }
        
        # Single product endpoint
        elif endpoint.startswith("/products/") and not endpoint.endswith("/candles"):
            product_id = endpoint.split("/")[2]
            base_prices = {
                "BTC-USD": 50000,
                "ETH-USD": 3000,
                "SOL-USD": 45,
                "ADA-USD": 0.5,
                "XRP-USD": 0.6
            }
            base_price = base_prices.get(product_id, 100)
            
            # Handle ticker endpoint specifically
            if endpoint.endswith("/ticker"):
                return {
                    "trade_id": random.randint(100000, 999999),
                    "price": f"{base_price * random.uniform(0.95, 1.05):.2f}",
                    "size": f"{random.uniform(0.1, 10):.4f}",
                    "time": datetime.now().isoformat(),
                    "bid": f"{base_price * random.uniform(0.94, 1.04):.2f}",
                    "ask": f"{base_price * random.uniform(0.96, 1.06):.2f}",
                    "volume": f"{random.uniform(10000, 100000):.2f}"
                }
            else:
                return {
                    "product_id": product_id,
                    "price": f"{base_price * random.uniform(0.95, 1.05):.2f}",
                    "volume_24h": f"{random.uniform(10000, 100000):.2f}",
                    "status": "online"
                }
        
        # Account endpoint
        elif endpoint == "/accounts":
            return {
                "accounts": [
                    {
                        "id": "demo-account-usd",
                        "currency": "USD",
                        "balance": "10000.00",
                        "available": "10000.00",
                        "hold": "0.00"
                    },
                    {
                        "id": "demo-account-btc",
                        "currency": "BTC",
                        "balance": "0.5",
                        "available": "0.5",
                        "hold": "0.00"
                    },
                    {
                        "id": "demo-account-eth",
                        "currency": "ETH",
                        "balance": "5.0",
                        "available": "5.0",
                        "hold": "0.00"
                    }
                ]
            }
        
        # Orders endpoint
        elif endpoint == "/orders":
            if method == "POST":
                # Create order
                return {
                    "id": "demo-order-" + datetime.now().strftime("%Y%m%d%H%M%S"),
                    "product_id": data.get("product_id", "BTC-USD"),
                    "side": data.get("side", "buy"),
                    "size": data.get("size", "0.01"),
                    "price": data.get("price", "50000"),
                    "status": "pending",
                    "created_at": datetime.now().isoformat()
                }
            else:
                # Get orders
                return {
                    "orders": [
                        {
                            "id": "demo-order-123",
                            "product_id": "BTC-USD",
                            "side": "buy",
                            "size": "0.01",
                            "price": "49500",
                            "status": "filled",
                            "created_at": (datetime.now() - timedelta(hours=1)).isoformat()
                        }
                    ]
                }
        
        # Default response for unknown endpoints
        return {"error": f"Demo endpoint not implemented: {endpoint}"}
    
    def get_candles(self, product_id: str, granularity: int = 3600, start: str = None, end: str = None) -> Dict[str, Any]:
        """
        Get historical candle data for a product.
        
        Args:
            product_id: Product ID (e.g., 'BTC-USD')
            granularity: Granularity in seconds (60, 300, 900, 3600, 21600, 86400)
            start: Start time in ISO format
            end: End time in ISO format
            
        Returns:
            Dictionary with candle data or error
        """
        try:
            if self.demo_mode:
                # Return demo candle data
                import random
                
                candles = []
                base_price = 50000 if "BTC" in product_id else 3000 if "ETH" in product_id else 100
                
                # Generate 100 demo candles
                for i in range(100):
                    timestamp = int((datetime.now() - timedelta(hours=100-i)).timestamp())
                    price_variation = random.uniform(-0.05, 0.05)
                    open_price = base_price * (1 + price_variation)
                    close_price = open_price * (1 + random.uniform(-0.02, 0.02))
                    high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.01))
                    low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.01))
                    volume = random.uniform(1000, 10000)
                    
                    candles.append({
                        "timestamp": timestamp,
                        "low": low_price,
                        "high": high_price,
                        "open": open_price,
                        "close": close_price,
                        "volume": volume
                    })
                
                return {"candles": candles}
            
            # Build URL for real API
            url = f"{self.base_url}/products/{product_id}/candles"
            
            # Build parameters
            params = {
                "granularity": granularity
            }
            
            if start:
                params["start"] = start
            if end:
                params["end"] = end
            
            # Make request
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                candles = response.json()
                
                # Convert to standard format
                formatted_candles = []
                for candle in candles:
                    if len(candle) >= 6:
                        formatted_candles.append({
                            "timestamp": candle[0],
                            "low": float(candle[1]),
                            "high": float(candle[2]),
                            "open": float(candle[3]),
                            "close": float(candle[4]),
                            "volume": float(candle[5])
                        })
                
                return {"candles": formatted_candles}
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        
        except Exception as e:
            return {"error": f"Error fetching candles: {e}"}
    
    def get_products(self) -> Dict[str, Any]:
        """Get all available products."""
        return self._make_request("GET", "/products")
    
    def get_product(self, product_id: str) -> Dict[str, Any]:
        """Get product information."""
        return self._make_request("GET", f"/products/{product_id}")
    
    def get_product_ticker(self, product_id: str) -> Dict[str, Any]:
        """Get product ticker information."""
        return self._make_request("GET", f"/products/{product_id}/ticker")
    
    def get_accounts(self) -> Dict[str, Any]:
        """Get account information."""
        return self._make_request("GET", "/accounts")
    
    def get_orders(self, status: str = "all") -> Dict[str, Any]:
        """Get orders."""
        params = {"status": status} if status != "all" else {}
        return self._make_request("GET", "/orders", params=params)
    
    def create_order(self, product_id: str, side: str, size: str, price: str = None, order_type: str = "limit") -> Dict[str, Any]:
        """Create an order."""
        data = {
            "product_id": product_id,
            "side": side,
            "size": size,
            "type": order_type
        }
        
        if order_type == "limit" and price:
            data["price"] = price
        
        return self._make_request("POST", "/orders", data=data)

class CoinGeckoClient:
    """Client for interacting with CoinGecko API."""
    
    def __init__(self):
        """Initialize CoinGecko client."""
        self.base_url = "https://api.coingecko.com/api/v3"
        self.last_request_time = 0
        self.rate_limit_delay = 1.0  # 1 second between requests
    
    def _rate_limit(self):
        """Implement rate limiting."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_request
            logger.warning(f"CoinGecko API rate limit reached. Retrying after delay.")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def get_coin_data(self, coin_id: str) -> Dict[str, Any]:
        """
        Get comprehensive coin data from CoinGecko.
        
        Args:
            coin_id: CoinGecko coin ID (e.g., 'bitcoin', 'ethereum')
            
        Returns:
            Dictionary with coin data or error
        """
        try:
            self._rate_limit()
            
            url = f"{self.base_url}/coins/{coin_id}"
            params = {
                "localization": "false",
                "tickers": "false",
                "market_data": "true",
                "community_data": "true",
                "developer_data": "true"
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        
        except Exception as e:
            return {"error": f"Error fetching coin data: {e}"}
    
    def get_fear_greed_index(self) -> Dict[str, Any]:
        """
        Get Fear & Greed Index data.
        
        Returns:
            Dictionary with fear & greed index data or error
        """
        try:
            self._rate_limit()
            
            url = "https://api.alternative.me/fng/"
            params = {"limit": "30"}  # Get last 30 days
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
        
        except Exception as e:
            return {"error": f"Error fetching fear & greed index: {e}"}

if __name__ == "__main__":
    # Example usage
    client = CoinbaseClient()
    
    # Get products
    products = client.get_products()
    print(f"Available products: {json.dumps(products, indent=2)}")
    
    # Get candles for BTC-USD
    candles = client.get_candles("BTC-USD", granularity=3600)  # 1-hour candles
    print(f"Got {len(candles.get('candles', []))} candles for BTC-USD")
    
    # Get accounts
    accounts = client.get_accounts()
    print(f"Accounts: {json.dumps(accounts, indent=2)}")
