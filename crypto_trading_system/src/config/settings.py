"""
Configuration settings for the Cryptocurrency Trading System.
"""

import os
from typing import List, Dict, Any

# API credentials
COINBASE_API_KEY = os.getenv("COINBASE_API_KEY", "")
COINBASE_API_SECRET = os.getenv("COINBASE_API_SECRET", "")
COINBASE_API_PASSPHRASE = os.getenv("COINBASE_API_PASSPHRASE", "")

# Demo mode (no real trades)
DEMO_MODE = os.getenv("DEMO_MODE", "True").lower() in ("true", "1", "t")

# Default trading pairs
DEFAULT_TRADING_PAIRS = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "ADA-USD",
    "XRP-USD",
    "DOT-USD",
    "DOGE-USD",
    "AVAX-USD",
    "MATIC-USD",
    "LINK-USD"
]

# Time intervals
TIME_INTERVALS = {
    "1h": 3600,      # 1 hour in seconds
    "1d": 86400,     # 1 day in seconds
    "7d": 604800,    # 7 days in seconds
    "30d": 2592000,  # 30 days in seconds
    "90d": 7776000   # 90 days in seconds
}

# Risk settings
RISK_SETTINGS = {
    "max_trade_size_percentage": 5.0,  # Maximum percentage of available balance to use in a single trade
    "stop_loss_percentage": 5.0,       # Stop loss percentage
    "take_profit_percentage": 10.0,    # Take profit percentage
    "max_open_positions": 5            # Maximum number of open positions
}

# Analysis settings
ANALYSIS_SETTINGS = {
    "technical_weight": 0.4,           # Weight for technical analysis
    "sentiment_weight": 0.2,           # Weight for sentiment analysis
    "market_weight": 0.2,              # Weight for market data analysis
    "project_weight": 0.2              # Weight for project fundamentals analysis
}

# Dashboard settings
DASHBOARD_SETTINGS = {
    "refresh_interval": 60,            # Dashboard refresh interval in seconds
    "theme": "dark",                   # Dashboard theme (dark or light)
    "default_interval": "1h",          # Default time interval
    "default_symbol": "BTC-USD"        # Default trading pair
}

# Railway deployment settings
RAILWAY_SETTINGS = {
    "port": int(os.getenv("PORT", "8050")),
    "host": "0.0.0.0",
    "debug": os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
}

# File paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")

# Create directories if they don't exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# File paths
ANALYSIS_RESULTS_FILE = os.path.join(DATA_DIR, "analysis_results.json")
PORTFOLIO_STATUS_FILE = os.path.join(DATA_DIR, "portfolio_status.json")
TRADE_HISTORY_FILE = os.path.join(DATA_DIR, "trade_history.json")
