"""
Sentiment analysis module for the Cryptocurrency Trading System.

This module provides functions for analyzing cryptocurrency sentiment data
from various sources including social media, news, and market indicators.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import requests
import pandas as pd
import numpy as np

from ..utils.helpers import setup_logging

# Set up logging
logger = setup_logging("sentiment_analysis")

def get_fear_greed_index(days: int = 30) -> Dict[str, Any]:
    """
    Fetch Fear & Greed Index data.
    
    Args:
        days: Number of days of historical data to fetch
        
    Returns:
        Dictionary with Fear & Greed Index data
    """
    logger.info(f"Fetching Fear & Greed Index data for the past {days} days")
    
    url = "https://api.alternative.me/fng/?limit=0"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if data["metadata"]["error"] is None:
            # Filter data for the requested number of days
            now = datetime.now()
            start_date = now - timedelta(days=days)
            
            filtered_data = []
            for item in data["data"]:
                timestamp = int(item["timestamp"])
                date = datetime.fromtimestamp(timestamp)
                if date >= start_date:
                    filtered_data.append(item)
            
            logger.info(f"Successfully fetched {len(filtered_data)} Fear & Greed Index data points")
            return {"data": filtered_data, "metadata": data["metadata"]}
        else:
            logger.error(f"API Error: {data['metadata']['error']}")
            return {}
    
    except Exception as e:
        logger.error(f"Error fetching Fear & Greed Index data: {e}")
        return {}

def get_social_sentiment(symbol: str) -> Dict[str, float]:
    """
    Fetch social media sentiment data for a cryptocurrency.
    
    Args:
        symbol: The trading pair symbol (e.g., 'BTC-USD')
        
    Returns:
        Dictionary with social sentiment scores
    """
    logger.info(f"Fetching social sentiment data for {symbol}")
    
    # Extract the base currency from the trading pair
    base_currency = symbol.split("-")[0]
    
    # In a real implementation, this would call a social sentiment API
    # For now, we'll return mock data
    mock_data = {
        "BTC": {"reddit": 0.65, "twitter": 0.72, "overall": 0.68},
        "ETH": {"reddit": 0.58, "twitter": 0.63, "overall": 0.60},
        "SOL": {"reddit": 0.75, "twitter": 0.68, "overall": 0.72},
        "ADA": {"reddit": 0.52, "twitter": 0.48, "overall": 0.50},
        "XRP": {"reddit": 0.45, "twitter": 0.52, "overall": 0.48}
    }
    
    if base_currency in mock_data:
        logger.info(f"Successfully fetched social sentiment data for {symbol}")
        return mock_data[base_currency]
    else:
        # Generate random sentiment data for unknown currencies
        import random
        random_sentiment = {
            "reddit": round(random.uniform(0.3, 0.8), 2),
            "twitter": round(random.uniform(0.3, 0.8), 2),
            "overall": round(random.uniform(0.3, 0.8), 2)
        }
        logger.info(f"Generated mock social sentiment data for {symbol}")
        return random_sentiment

def get_news_sentiment(symbol: str) -> Dict[str, float]:
    """
    Fetch news sentiment data for a cryptocurrency.
    
    Args:
        symbol: The trading pair symbol (e.g., 'BTC-USD')
        
    Returns:
        Dictionary with news sentiment scores
    """
    logger.info(f"Fetching news sentiment data for {symbol}")
    
    # Extract the base currency from the trading pair
    base_currency = symbol.split("-")[0]
    
    # In a real implementation, this would call a news sentiment API
    # For now, we'll return mock data
    mock_data = {
        "BTC": {"positive": 0.58, "negative": 0.22, "neutral": 0.20, "overall": 0.36},
        "ETH": {"positive": 0.62, "negative": 0.18, "neutral": 0.20, "overall": 0.44},
        "SOL": {"positive": 0.70, "negative": 0.15, "neutral": 0.15, "overall": 0.55},
        "ADA": {"positive": 0.55, "negative": 0.25, "neutral": 0.20, "overall": 0.30},
        "XRP": {"positive": 0.48, "negative": 0.32, "neutral": 0.20, "overall": 0.16}
    }
    
    if base_currency in mock_data:
        logger.info(f"Successfully fetched news sentiment data for {symbol}")
        return mock_data[base_currency]
    else:
        # Generate random sentiment data for unknown currencies
        import random
        positive = round(random.uniform(0.3, 0.7), 2)
        negative = round(random.uniform(0.1, 0.4), 2)
        neutral = round(1 - positive - negative, 2)
        overall = round(positive - negative, 2)
        
        random_sentiment = {
            "positive": positive,
            "negative": negative,
            "neutral": neutral,
            "overall": overall
        }
        logger.info(f"Generated mock news sentiment data for {symbol}")
        return random_sentiment

def score_fear_greed_index(fear_greed_data: Dict[str, Any], interval: str = "1d") -> float:
    """
    Score Fear & Greed Index data.
    
    Args:
        fear_greed_data: Fear & Greed Index data
        interval: The time interval for analysis ('1h', '1d', '7d', '30d', '90d')
        
    Returns:
        Score between -1.0 and 1.0
    """
    if not fear_greed_data or "data" not in fear_greed_data or not fear_greed_data["data"]:
        logger.warning("No Fear & Greed Index data provided")
        return 0.0
    
    try:
        # Get the most recent data point
        latest = fear_greed_data["data"][0]
        value = int(latest["value"])
        
        # For 1-hour interval, we need to be more responsive to recent changes
        if interval == "1h":
            # If we have at least 24 data points (roughly 1 day), check for rapid changes
            if len(fear_greed_data["data"]) >= 24:
                # Compare current value with the value from ~6 hours ago
                previous = fear_greed_data["data"][6]
                previous_value = int(previous["value"])
                
                # Calculate change rate
                change = value - previous_value
                
                # If there's a significant rapid change, amplify the signal
                if abs(change) > 10:
                    logger.info(f"Detected significant rapid change in Fear & Greed Index: {change}")
                    # Normalize to [-1, 1] range with amplification for rapid changes
                    return (value - 50) / 50 * (1 + abs(change) / 50)
        
        # Standard scoring for all intervals
        # Normalize to [-1, 1] range
        # Values below 50 (fear) become negative, values above 50 (greed) become positive
        score = (value - 50) / 50
        
        logger.info(f"Fear & Greed Index score: {score:.2f}")
        return score
    
    except Exception as e:
        logger.error(f"Error scoring Fear & Greed Index: {e}")
        return 0.0

def score_social_sentiment(social_data: Dict[str, float]) -> float:
    """
    Score social media sentiment data.
    
    Args:
        social_data: Social sentiment data
        
    Returns:
        Score between -1.0 and 1.0
    """
    if not social_data or "overall" not in social_data:
        logger.warning("No social sentiment data provided")
        return 0.0
    
    try:
        # Convert from [0, 1] range to [-1, 1] range
        score = (social_data["overall"] - 0.5) * 2
        
        logger.info(f"Social sentiment score: {score:.2f}")
        return score
    
    except Exception as e:
        logger.error(f"Error scoring social sentiment: {e}")
        return 0.0

def score_news_sentiment(news_data: Dict[str, float]) -> float:
    """
    Score news sentiment data.
    
    Args:
        news_data: News sentiment data
        
    Returns:
        Score between -1.0 and 1.0
    """
    if not news_data or "overall" not in news_data:
        logger.warning("No news sentiment data provided")
        return 0.0
    
    try:
        # Convert from [-1, 1] range (if needed)
        if -1 <= news_data["overall"] <= 1:
            score = news_data["overall"]
        else:
            # Assume it's in [0, 1] range and convert to [-1, 1]
            score = (news_data["overall"] - 0.5) * 2
        
        logger.info(f"News sentiment score: {score:.2f}")
        return score
    
    except Exception as e:
        logger.error(f"Error scoring news sentiment: {e}")
        return 0.0

def analyze_sentiment(symbol: str, interval: str = "1d") -> Dict[str, float]:
    """
    Perform sentiment analysis for a cryptocurrency.
    
    Args:
        symbol: The trading pair symbol (e.g., 'BTC-USD')
        interval: The time interval for analysis ('1h', '1d', '7d', '30d', '90d')
        
    Returns:
        Dictionary with sentiment analysis scores
    """
    logger.info(f"Starting sentiment analysis for {symbol} with interval {interval}")
    
    # Determine the number of days to fetch based on interval
    days_map = {
        "1h": 1,
        "1d": 7,
        "7d": 14,
        "30d": 60,
        "90d": 120
    }
    days = days_map.get(interval, 30)
    
    # Get Fear & Greed Index data
    fear_greed_data = get_fear_greed_index(days)
    
    # Get social sentiment data
    social_data = get_social_sentiment(symbol)
    
    # Get news sentiment data
    news_data = get_news_sentiment(symbol)
    
    # Score sentiment data
    scores = {}
    
    # Fear & Greed Index score
    if fear_greed_data:
        scores["fear_greed"] = score_fear_greed_index(fear_greed_data, interval)
    
    # Social sentiment score
    if social_data:
        scores["social"] = score_social_sentiment(social_data)
    
    # News sentiment score
    if news_data:
        scores["news"] = score_news_sentiment(news_data)
    
    # Overall sentiment score (weighted average)
    weights = {
        "fear_greed": 0.4,
        "social": 0.3,
        "news": 0.3
    }
    
    # Adjust weights based on available data
    available_categories = [cat for cat in weights.keys() if cat in scores]
    if not available_categories:
        logger.warning("No sentiment data available")
        return {}
    
    # Normalize weights based on available data
    total_weight = sum(weights[cat] for cat in available_categories)
    normalized_weights = {cat: weights[cat] / total_weight for cat in available_categories}
    
    # Calculate overall score
    overall_score = sum(scores[cat] * normalized_weights[cat] for cat in available_categories)
    scores["overall"] = overall_score
    
    logger.info(f"Sentiment analysis scores: {scores}")
    return scores

if __name__ == "__main__":
    # Example usage
    symbol = "BTC-USD"
    scores = analyze_sentiment(symbol, interval="1h")
    print(f"Sentiment analysis scores for {symbol}: {scores}")
