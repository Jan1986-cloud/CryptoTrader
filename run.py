#!/usr/bin/env python3

"""
Runner script for the Cryptocurrency Trading System.

This script provides a simple command-line interface to run the system.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from crypto_trading_system.src.main import main

if __name__ == "__main__":
    main()
