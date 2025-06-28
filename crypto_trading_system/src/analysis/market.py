"""
Market data analysis module for cryptocurrency trading.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, timedelta

from ..models.data_models import MarketData
from ..utils.helpers import logger
from ..api.clients import CoinbaseClient, CoinGeckoClient
from ..config import settings

class MarketAnalyzer:
    """
    Class for analyzing market data related to cryptocurrencies.
    """
    
    def __init__(self):
        """Initialize the market analyzer."""
        self.coinbase_client = CoinbaseClient()
        self.coingecko_client = CoinGeckoClient()
    
    def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """
        Get current market data for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTC-USD")
            
        Returns:
            MarketData object or None if an error occurred
        """
        try:
            # Get ticker data from Coinbase
            ticker = self.coinbase_client.get_product_ticker(symbol)
            
            if not ticker:
                logger.warning(f"Failed to get ticker data for {symbol}")
                return None
            
            # Extract price and other available data
            price = float(ticker.get("price", 0))
            
            # Try to get additional market data from CoinGecko
            # First, convert symbol to CoinGecko ID
            coin_id = self._symbol_to_coingecko_id(symbol)
            market_cap = None
            volume_24h = None
            price_change_24h = None
            price_change_percentage_24h = None
            
            if coin_id:
                coin_data = self.coingecko_client.get_coin_data(coin_id)
                if coin_data and "market_data" in coin_data:
                    market_data = coin_data["market_data"]
                    market_cap = market_data.get("market_cap", {}).get("usd")
                    volume_24h = market_data.get("total_volume", {}).get("usd")
                    price_change_24h = market_data.get("price_change_24h")
                    price_change_percentage_24h = market_data.get("price_change_percentage_24h")
            
            return MarketData(
                timestamp=datetime.now(),
                symbol=symbol,
                price=price,
                market_cap=market_cap,
                volume_24h=volume_24h,
                price_change_percentage_24h=price_change_percentage_24h
            )
        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None
    
    def _symbol_to_coingecko_id(self, symbol: str) -> Optional[str]:
        """
        Convert a trading symbol to a CoinGecko coin ID.
        
        Args:
            symbol: Trading symbol (e.g., "BTC-USD")
            
        Returns:
            CoinGecko coin ID or None if not found
        """
        # Simple mapping for common symbols
        symbol_map = {
            "BTC-USD": "bitcoin",
            "ETH-USD": "ethereum",
            "SOL-USD": "solana",
            "LINK-USD": "chainlink",
            "AVAX-USD": "avalanche-2",
            "DOT-USD": "polkadot",
            "ADA-USD": "cardano",
            "XRP-USD": "ripple",
            "DOGE-USD": "dogecoin",
            "MATIC-USD": "matic-network"
        }
        
        # Check if symbol is in the map
        if symbol in symbol_map:
            return symbol_map[symbol]
        
        # If not in map, try to extract the base currency and search for it
        base_currency = symbol.split('-')[0].lower()
        
        try:
            # Get list of coins from CoinGecko
            coins = self.coingecko_client.get_coin_list()
            
            # Search for matching coin
            for coin in coins:
                if coin.get("symbol", "").lower() == base_currency:
                    return coin.get("id")
            
            logger.warning(f"Could not find CoinGecko ID for symbol {symbol}")
            return None
        except Exception as e:
            logger.error(f"Error converting symbol {symbol} to CoinGecko ID: {e}")
            return None
    
    def score_market_cap(self, market_cap: Optional[float]) -> int:
        """
        Score market cap based on its value.
        
        Args:
            market_cap: Market capitalization in USD
            
        Returns:
            Score from -2 to +2
        """
        if market_cap is None:
            return 0
        
        # Large cap (more stable)
        if market_cap > 100e9:  # > $100B
            return 1
        # Mid cap
        elif market_cap > 10e9:  # > $10B
            return 0
        # Small cap
        elif market_cap > 1e9:  # > $1B
            return -1
        # Micro cap (more volatile)
        else:
            return -2
    
    def score_volume(self, volume_24h: Optional[float], market_cap: Optional[float]) -> int:
        """
        Score trading volume based on its value and relation to market cap.
        
        Args:
            volume_24h: 24-hour trading volume in USD
            market_cap: Market capitalization in USD
            
        Returns:
            Score from -2 to +2
        """
        if volume_24h is None:
            return 0
        
        # If we have both volume and market cap, calculate volume/market cap ratio
        if market_cap is not None and market_cap > 0:
            ratio = volume_24h / market_cap
            
            # High volume relative to market cap (high liquidity, potentially bullish)
            if ratio > 0.25:
                return 1
            # Very low volume relative to market cap (low liquidity, potentially bearish)
            elif ratio < 0.05:
                return -1
        
        # Fallback to absolute volume if market cap is not available
        if volume_24h > 1e9:  # > $1B
            return 1
        elif volume_24h < 10e6:  # < $10M
            return -1
        
        return 0
    
    def score_price_change(self, price_change_percentage_24h: Optional[float]) -> int:
        """
        Score 24-hour price change percentage.
        
        Args:
            price_change_percentage_24h: 24-hour price change percentage
            
        Returns:
            Score from -2 to +2
        """
        if price_change_percentage_24h is None:
            return 0
        
        # Strong uptrend
        if price_change_percentage_24h > 10:
            return 2
        # Moderate uptrend
        elif price_change_percentage_24h > 5:
            return 1
        # Strong downtrend
        elif price_change_percentage_24h < -10:
            return -2
        # Moderate downtrend
        elif price_change_percentage_24h < -5:
            return -1
        # Relatively stable
        else:
            return 0


def analyze_market(symbol: str, interval: str = "1d") -> Dict[str, float]:
    """
    Analyze market data for a cryptocurrency symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTC-USD")
        interval: Time interval for analysis
        
    Returns:
        Dictionary containing market analysis scores
    """
    analyzer = MarketAnalyzer()
    
    try:
        # Get market data
        market_data = analyzer.get_market_data(symbol)
        
        if not market_data:
            logger.warning(f"Failed to get market data for {symbol}")
            return {
                "market_cap_score": 0.0,
                "volume_score": 0.0,
                "price_change_score": 0.0,
                "overall_market_score": 0.0
            }
        
        # Calculate scores
        market_cap_score = analyzer.score_market_cap(market_data.market_cap)
        volume_score = analyzer.score_volume(market_data.volume_24h, market_data.market_cap)
        price_change_score = analyzer.score_price_change(market_data.price_change_percentage_24h)
        
        # Calculate overall market score (weighted average)
        overall_score = (
            market_cap_score * 0.3 +
            volume_score * 0.4 +
            price_change_score * 0.3
        )
        
        return {
            "market_cap_score": float(market_cap_score),
            "volume_score": float(volume_score),
            "price_change_score": float(price_change_score),
            "overall_market_score": float(overall_score)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing market data for {symbol}: {e}")
        return {
            "market_cap_score": 0.0,
            "volume_score": 0.0,
            "price_change_score": 0.0,
            "overall_market_score": 0.0
        }

