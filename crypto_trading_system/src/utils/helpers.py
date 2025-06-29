"""
Utility functions for the Cryptocurrency Trading System.
"""

import os
import json
import logging
import os.path
from datetime import datetime
from typing import Dict, Any, Optional
from ..config.settings import LOGS_DIR

# Set up logging
def setup_logging(name: str) -> logging.Logger:
    """
    Set up logging for a module.
    
    Args:
        name: Module name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create console handler
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
        
        # Create logs directory if it doesn't exist
        os.makedirs(LOGS_DIR, exist_ok=True)

        # Create file handler
        file_handler = logging.FileHandler(os.path.join(LOGS_DIR, f"{name}.log"))
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        # Add file handler to logger
        logger.addHandler(file_handler)
    
    return logger

# Create a global logger
logger = setup_logging('crypto_trading_system')

def save_to_json(data: Dict[str, Any], filepath: str) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        filepath: Path to save the data
        
    Returns:
        True if successful, False otherwise
    """
    if not filepath or not isinstance(filepath, str) or not filepath.strip():
        logger.error(f"Invalid filepath provided for save_to_json: '{filepath}'")
        return False
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Data saved to {filepath}")
        return True
    
    except Exception as e:
        logger.error(f"Error saving data to {filepath}: {e}")
        return False

def load_from_json(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load data from a JSON file.
    
    Args:
        filepath: Path to load the data from
        
    Returns:
        Loaded data or None if error
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        logger.info(f"Data loaded from {filepath}")
        return data
    
    except Exception as e:
        logger.error(f"Error loading data from {filepath}: {e}")
        return None

def format_currency(value: float, currency: str = 'USD', precision: int = 2) -> str:
    """
    Format a currency value.
    
    Args:
        value: Value to format
        currency: Currency code
        precision: Decimal precision
        
    Returns:
        Formatted currency string
    """
    if currency == 'USD':
        return f"${value:,.{precision}f}"
    else:
        return f"{value:,.{precision}f} {currency}"

def format_percentage(value: float, precision: int = 2) -> str:
    """
    Format a percentage value.
    
    Args:
        value: Value to format (0.01 = 1%)
        precision: Decimal precision
        
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{precision}f}%"

def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.
    
    Returns:
        Current timestamp
    """
    return datetime.now().isoformat()

def create_directory_if_not_exists(directory: str) -> bool:
    """
    Create a directory if it doesn't exist.
    
    Args:
        directory: Directory path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.makedirs(directory, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {e}")
        return False
