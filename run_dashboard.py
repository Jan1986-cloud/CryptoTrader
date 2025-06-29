"""
Dashboard runner script for the Cryptocurrency Trading System.

This script runs the dashboard UI.
"""

import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from crypto_trading_system.src.ui.dashboard import run_dashboard

if __name__ == "__main__":
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DEBUG", "False").lower() == "true"
    
    run_dashboard(host="0.0.0.0", port=port, debug=debug)
