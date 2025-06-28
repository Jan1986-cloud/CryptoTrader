"""
Main application module for the Cryptocurrency Trading System.
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

from .config import settings
from .utils.helpers import setup_logging, save_to_json
from .api.clients import CoinbaseClient, CoinGeckoClient
from .analysis.orchestrator import AnalysisOrchestrator
from .trading.engine import TradingEngine

# Set up logging
logger = setup_logging("main")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Cryptocurrency Trading System")
    
    parser.add_argument("--analyze", action="store_true", help="Run analysis on trading pairs")
    parser.add_argument("--symbols", nargs="+", help="Trading symbols to analyze (e.g., BTC-USD ETH-USD)")
    parser.add_argument("--trade", action="store_true", help="Execute trades based on analysis")
    parser.add_argument("--demo", action="store_true", help="Run in demo mode (no real trades)")
    parser.add_argument("--output", help="Output file path for analysis results")
    
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    args = parse_arguments()
    
    logger.info("Starting Cryptocurrency Trading System")
    
    # Set demo mode from arguments or settings
    demo_mode = args.demo if args.demo is not None else settings.DEMO_MODE
    
    # Initialize trading engine
    trading_engine = TradingEngine(demo_mode=demo_mode)
    
    # Run analysis if requested
    if args.analyze:
        symbols = args.symbols if args.symbols else settings.DEFAULT_TRADING_PAIRS
        logger.info(f"Running analysis on symbols: {', '.join(symbols)}")
        
        # Initialize analysis orchestrator
        orchestrator = AnalysisOrchestrator()
        
        # Run analysis
        results = orchestrator.analyze_all_symbols(symbols)
        
        # Save results if output path is provided
        if args.output:
            output_path = args.output
        else:
            # Default output path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = os.path.join(settings.DATA_DIR, f"analysis_results_{timestamp}.json")
        
        orchestrator.save_analysis_results(results, output_path)
        logger.info(f"Analysis results saved to {output_path}")
        
        # Execute trades if requested
        if args.trade:
            logger.info("Executing trades based on analysis results")
            
            for symbol, result in results.items():
                trading_engine.execute_signal(symbol, result.signal, result.price)
            
            # Update portfolio after trading
            trading_engine.update_portfolio()
            
            # Save portfolio summary
            portfolio_summary = trading_engine.get_portfolio_summary()
            portfolio_path = os.path.join(settings.DATA_DIR, f"portfolio_{timestamp}.json")
            save_to_json(portfolio_summary, portfolio_path)
            logger.info(f"Portfolio summary saved to {portfolio_path}")
    
    logger.info("Cryptocurrency Trading System completed")

if __name__ == "__main__":
    main()
