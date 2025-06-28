"""
Models module for the Cryptocurrency Trading System.

This module defines data models used throughout the system.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any, Union


class TradingSignal(Enum):
    """Trading signal enumeration."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    NEUTRAL = "NEUTRAL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


@dataclass
class VariableScore:
    """Score for a single analysis variable."""
    name: str
    value: float
    score: float  # Normalized score between -1.0 and 1.0
    weight: float
    description: str


@dataclass
class AnalysisResult:
    """Result of cryptocurrency analysis."""
    timestamp: datetime
    symbol: str
    coin_id: Optional[str]
    price: Optional[float]
    scores: List[VariableScore]
    final_score: float
    signal: TradingSignal
    confidence: float


@dataclass
class TechnicalIndicators:
    """Technical indicators for a cryptocurrency."""
    symbol: str
    timestamp: datetime
    rsi_14: Optional[float] = None
    macd_line: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    atr_14: Optional[float] = None
    volume_24h: Optional[float] = None


@dataclass
class SentimentData:
    """Sentiment data for a cryptocurrency."""
    timestamp: datetime
    fear_greed_value: Optional[int] = None
    fear_greed_classification: Optional[str] = None
    social_sentiment: Optional[float] = None
    news_sentiment: Optional[float] = None


@dataclass
class MarketData:
    """Market data for a cryptocurrency."""
    symbol: str
    timestamp: datetime
    price: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None
    price_change_percentage_7d: Optional[float] = None
    price_change_percentage_30d: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    max_supply: Optional[float] = None


@dataclass
class ProjectData:
    """Project fundamental data for a cryptocurrency."""
    coin_id: str
    timestamp: datetime
    developer_score: Optional[float] = None
    community_score: Optional[float] = None
    liquidity_score: Optional[float] = None
    public_interest_score: Optional[float] = None
    github_stats: Optional[Dict[str, Any]] = None
    reddit_stats: Optional[Dict[str, Any]] = None
    twitter_stats: Optional[Dict[str, Any]] = None


@dataclass
class TradeExecution:
    """Trade execution details."""
    timestamp: datetime
    symbol: str
    action: str  # BUY, SELL, HOLD
    price: float
    quantity: float
    total: float
    order_id: Optional[str] = None
    status: str = "PENDING"  # PENDING, EXECUTED, FAILED
    error: Optional[str] = None


@dataclass
class Portfolio:
    """Portfolio status."""
    timestamp: datetime
    total_value_usd: float
    assets: List[Dict[str, Any]]
    performance_24h: Optional[float] = None
    performance_7d: Optional[float] = None
    performance_30d: Optional[float] = None
