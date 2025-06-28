"""
Technical analysis module for the Cryptocurrency Trading System.

This module provides functions for analyzing cryptocurrency price data
using various technical indicators.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import pandas as pd
import numpy as np
import requests
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands
from ta.volume import OnBalanceVolumeIndicator

from ..utils.helpers import setup_logging

# Set up logging
logger = setup_logging("technical_analysis")

def get_historical_data(symbol: str, interval: str = "1d", days: int = 30) -> pd.DataFrame:
    """
    Fetch historical price data for a cryptocurrency.
    
    Args:
        symbol: The trading pair symbol (e.g., 'BTC-USD')
        interval: The time interval ('1h', '1d', '7d', '30d', '90d')
        days: Number of days of historical data to fetch
        
    Returns:
        DataFrame with historical price data
    """
    logger.info(f"Fetching historical data for {symbol} with interval {interval}")
    
    # Convert interval to seconds for API request
    interval_seconds = {
        "1h": 3600,
        "1d": 86400,
        "7d": 604800,
        "30d": 2592000,
        "90d": 7776000
    }
    
    # Calculate start and end dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Format dates for API request
    start_date_str = start_date.strftime("%Y-%m-%dT%H:%M:%S")
    end_date_str = end_date.strftime("%Y-%m-%dT%H:%M:%S")
    
    # Coinbase API endpoint
    url = f"https://api.exchange.coinbase.com/products/{symbol}/candles"
    
    # Parameters for API request
    params = {
        "granularity": interval_seconds.get(interval, 86400),
        "start": start_date_str,
        "end": end_date_str
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Create DataFrame from response
        df = pd.DataFrame(data, columns=["time", "low", "high", "open", "close", "volume"])
        df["time"] = pd.to_datetime(df["time"], unit="s")
        df.set_index("time", inplace=True)
        df.sort_index(inplace=True)
        
        logger.info(f"Successfully fetched {len(df)} data points for {symbol}")
        return df
    
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def calculate_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate technical indicators for price data.
    
    Args:
        df: DataFrame with price data
        
    Returns:
        DataFrame with technical indicators
    """
    if df.empty:
        logger.warning("Empty DataFrame provided, cannot calculate indicators")
        return df
    
    try:
        # Moving Averages
        df["sma_20"] = SMAIndicator(close=df["close"], window=20).sma_indicator()
        df["sma_50"] = SMAIndicator(close=df["close"], window=50).sma_indicator()
        df["ema_12"] = EMAIndicator(close=df["close"], window=12).ema_indicator()
        df["ema_26"] = EMAIndicator(close=df["close"], window=26).ema_indicator()
        
        # MACD
        macd = MACD(close=df["close"], window_slow=26, window_fast=12, window_sign=9)
        df["macd"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_diff"] = macd.macd_diff()
        
        # RSI
        df["rsi"] = RSIIndicator(close=df["close"], window=14).rsi()
        
        # Bollinger Bands
        bollinger = BollingerBands(close=df["close"], window=20, window_dev=2)
        df["bb_high"] = bollinger.bollinger_hband()
        df["bb_low"] = bollinger.bollinger_lband()
        df["bb_mid"] = bollinger.bollinger_mavg()
        df["bb_width"] = (df["bb_high"] - df["bb_low"]) / df["bb_mid"]
        
        # Stochastic Oscillator
        stoch = StochasticOscillator(high=df["high"], low=df["low"], close=df["close"], window=14, smooth_window=3)
        df["stoch_k"] = stoch.stoch()
        df["stoch_d"] = stoch.stoch_signal()
        
        # Volume indicators
        df["obv"] = OnBalanceVolumeIndicator(close=df["close"], volume=df["volume"]).on_balance_volume()
        
        # Price change indicators
        df["price_change_1d"] = df["close"].pct_change(1)
        df["price_change_7d"] = df["close"].pct_change(7)
        
        # Special 1-hour indicators for rapid trading (especially for altcoins)
        if len(df) >= 24:  # Ensure we have enough data points
            df["price_change_1h"] = df["close"].pct_change(1)
            df["volatility_1h"] = df["close"].rolling(window=6).std() / df["close"].rolling(window=6).mean()
            df["volume_change_1h"] = df["volume"].pct_change(1)
            
            # Momentum indicators for 1-hour timeframe
            df["rsi_1h"] = RSIIndicator(close=df["close"], window=6).rsi()
            
            # Rapid movement detection (for altcoin signals)
            df["rapid_rise"] = ((df["price_change_1h"] > 0.03) & (df["volume_change_1h"] > 0.05)).astype(int)
            df["rapid_fall"] = ((df["price_change_1h"] < -0.03) & (df["volume_change_1h"] > 0.05)).astype(int)
        
        logger.info("Successfully calculated technical indicators")
        return df
    
    except Exception as e:
        logger.error(f"Error calculating technical indicators: {e}")
        return df

def score_technical_indicators(df: pd.DataFrame) -> Dict[str, float]:
    """
    Score technical indicators to generate trading signals.
    
    Args:
        df: DataFrame with technical indicators
        
    Returns:
        Dictionary with scores for different technical aspects
    """
    if df.empty:
        logger.warning("Empty DataFrame provided, cannot score indicators")
        return {}
    
    try:
        # Get the most recent data point
        latest = df.iloc[-1]
        
        scores = {}
        
        # Trend scores
        trend_score = 0
        
        # Moving average relationships
        if latest["close"] > latest["sma_20"]:
            trend_score += 0.2
        if latest["close"] > latest["sma_50"]:
            trend_score += 0.2
        if latest["sma_20"] > latest["sma_50"]:
            trend_score += 0.2
        if latest["ema_12"] > latest["ema_26"]:
            trend_score += 0.2
            
        # MACD
        if latest["macd"] > latest["macd_signal"]:
            trend_score += 0.2
        elif latest["macd"] < latest["macd_signal"]:
            trend_score -= 0.2
            
        scores["trend"] = min(max(trend_score, -1.0), 1.0)
        
        # Momentum scores
        momentum_score = 0
        
        # RSI
        if latest["rsi"] < 30:
            momentum_score += 0.3  # Oversold
        elif latest["rsi"] > 70:
            momentum_score -= 0.3  # Overbought
        
        # Stochastic
        if latest["stoch_k"] < 20 and latest["stoch_d"] < 20:
            momentum_score += 0.3  # Oversold
        elif latest["stoch_k"] > 80 and latest["stoch_d"] > 80:
            momentum_score -= 0.3  # Overbought
            
        # Recent price changes
        if latest["price_change_1d"] > 0:
            momentum_score += 0.2
        else:
            momentum_score -= 0.1
            
        if latest["price_change_7d"] > 0:
            momentum_score += 0.2
        else:
            momentum_score -= 0.1
            
        scores["momentum"] = min(max(momentum_score, -1.0), 1.0)
        
        # Volatility scores
        volatility_score = 0
        
        # Bollinger Bands
        bb_position = (latest["close"] - latest["bb_low"]) / (latest["bb_high"] - latest["bb_low"])
        if bb_position < 0.2:
            volatility_score += 0.3  # Near lower band, potential buy
        elif bb_position > 0.8:
            volatility_score -= 0.3  # Near upper band, potential sell
            
        # Bollinger Band width
        if latest["bb_width"] > df["bb_width"].mean() * 1.5:
            volatility_score -= 0.2  # High volatility, caution
            
        scores["volatility"] = min(max(volatility_score, -1.0), 1.0)
        
        # Volume scores
        volume_score = 0
        
        # OBV trend
        obv_change = (latest["obv"] - df["obv"].iloc[-10]) / abs(df["obv"].iloc[-10]) if abs(df["obv"].iloc[-10]) > 0 else 0
        if obv_change > 0.05:
            volume_score += 0.3
        elif obv_change < -0.05:
            volume_score -= 0.3
            
        # Recent volume changes
        if "volume_change_1h" in latest and latest["volume_change_1h"] > 0.1:
            volume_score += 0.2
            
        scores["volume"] = min(max(volume_score, -1.0), 1.0)
        
        # Special 1-hour rapid trading signals (especially for altcoins)
        if "rapid_rise" in latest:
            rapid_trading_score = 0
            
            # Check for rapid price movements
            if latest["rapid_rise"] == 1:
                rapid_trading_score += 0.5
                logger.info("Detected rapid rise signal")
            if latest["rapid_fall"] == 1:
                rapid_trading_score -= 0.5
                logger.info("Detected rapid fall signal")
                
            # Check short-term RSI
            if "rsi_1h" in latest:
                if latest["rsi_1h"] < 20:
                    rapid_trading_score += 0.3  # Extremely oversold in short term
                elif latest["rsi_1h"] > 80:
                    rapid_trading_score -= 0.3  # Extremely overbought in short term
            
            # Check short-term volatility
            if "volatility_1h" in latest and latest["volatility_1h"] > df["volatility_1h"].mean() * 2:
                # High short-term volatility detected
                if latest["price_change_1h"] > 0:
                    rapid_trading_score += 0.2  # Upward volatility
                else:
                    rapid_trading_score -= 0.2  # Downward volatility
            
            scores["rapid_trading"] = min(max(rapid_trading_score, -1.0), 1.0)
        
        # Overall technical score (weighted average)
        weights = {
            "trend": 0.3,
            "momentum": 0.25,
            "volatility": 0.2,
            "volume": 0.15,
            "rapid_trading": 0.1 if "rapid_trading" in scores else 0
        }
        
        # Adjust weights if rapid_trading is not available
        if "rapid_trading" not in scores:
            weights["trend"] += 0.05
            weights["momentum"] += 0.05
        
        overall_score = sum(scores[k] * weights[k] for k in scores) / sum(weights[k] for k in scores if k in scores)
        scores["overall"] = min(max(overall_score, -1.0), 1.0)
        
        logger.info(f"Technical analysis scores: {scores}")
        return scores
    
    except Exception as e:
        logger.error(f"Error scoring technical indicators: {e}")
        return {}

def analyze_technical(symbol: str, interval: str = "1d", days: int = 30) -> Dict[str, float]:
    """
    Perform technical analysis for a cryptocurrency.
    
    Args:
        symbol: The trading pair symbol (e.g., 'BTC-USD')
        interval: The time interval ('1h', '1d', '7d', '30d', '90d')
        days: Number of days of historical data to analyze
        
    Returns:
        Dictionary with technical analysis scores
    """
    logger.info(f"Starting technical analysis for {symbol} with interval {interval}")
    
    # Get historical data
    df = get_historical_data(symbol, interval, days)
    if df.empty:
        logger.error(f"Failed to get historical data for {symbol}")
        return {}
    
    # Calculate technical indicators
    df = calculate_technical_indicators(df)
    
    # Score technical indicators
    scores = score_technical_indicators(df)
    
    logger.info(f"Completed technical analysis for {symbol}")
    return scores

if __name__ == "__main__":
    # Example usage
    symbol = "BTC-USD"
    scores = analyze_technical(symbol, interval="1h", days=7)
    print(f"Technical analysis scores for {symbol}: {scores}")
