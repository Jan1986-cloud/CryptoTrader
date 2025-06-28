"""
Package initialization file for the Cryptocurrency Trading System.
"""

from .config import settings
from .utils.helpers import setup_logging

# Set up default logger
logger = setup_logging("crypto_trading_system")
