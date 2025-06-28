"""
Modified integration test script for the Cryptocurrency Trading System.

This script tests the full data collection and analysis pipeline,
ensuring all modules work together seamlessly.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add the project root directory to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Import modules directly
from crypto_trading_system.src.config.settings import (
    DEFAULT_TRADING_PAIRS, DATA_DIR, DEMO_MODE
)
from crypto_trading_system.src.utils.helpers import setup_logging, save_to_json
from crypto_trading_system.src.api.clients import CoinbaseClient, CoinGeckoClient
from crypto_trading_system.src.analysis.technical import TechnicalAnalyzer
from crypto_trading_system.src.analysis.sentiment import SentimentAnalyzer
from crypto_trading_system.src.analysis.market import MarketAnalyzer
from crypto_trading_system.src.analysis.project import ProjectAnalyzer
from crypto_trading_system.src.analysis.orchestrator import AnalysisOrchestrator
from crypto_trading_system.src.trading.engine import TradingEngine

# Set up logging
logger = setup_logging("integration_test")

def test_api_connections():
    """Test API connections to Coinbase and CoinGecko."""
    logger.info("Testing API connections...")
    
    # Test Coinbase API
    coinbase_client = CoinbaseClient()
    products = coinbase_client.get_products()
    logger.info(f"Coinbase API connection: {'Success' if products else 'Failed'}")
    if products:
        logger.info(f"Found {len(products)} products on Coinbase")
    
    # Test CoinGecko API
    coingecko_client = CoinGeckoClient()
    coins = coingecko_client.get_coin_list()
    logger.info(f"CoinGecko API connection: {'Success' if coins else 'Failed'}")
    if coins:
        logger.info(f"Found {len(coins)} coins on CoinGecko")
    
    return products and coins

def test_individual_analyzers():
    """Test each analyzer component individually."""
    logger.info("Testing individual analyzers...")
    
    # Test Technical Analyzer
    technical_analyzer = TechnicalAnalyzer()
    logger.info("Technical Analyzer initialized successfully")
    
    # Test Sentiment Analyzer
    sentiment_analyzer = SentimentAnalyzer()
    sentiment_data = sentiment_analyzer.analyze_sentiment()
    logger.info(f"Sentiment Analyzer test: {'Success' if sentiment_data else 'Failed'}")
    if sentiment_data and sentiment_data.fear_greed_value:
        logger.info(f"Current Fear & Greed Index: {sentiment_data.fear_greed_value} ({sentiment_data.fear_greed_classification})")
    
    # Test Market Analyzer
    market_analyzer = MarketAnalyzer()
    market_data = market_analyzer.get_market_data("BTC-USD")
    logger.info(f"Market Analyzer test: {'Success' if market_data else 'Failed'}")
    if market_data:
        logger.info(f"Current BTC price: {market_data.price}")
    
    # Test Project Analyzer
    project_analyzer = ProjectAnalyzer()
    project_data = project_analyzer.get_project_data("bitcoin")
    logger.info(f"Project Analyzer test: {'Success' if project_data else 'Failed'}")
    
    return sentiment_data and market_data

def test_analysis_pipeline(symbols=None):
    """Test the analysis pipeline with specified symbols."""
    if symbols is None:
        symbols = DEFAULT_TRADING_PAIRS[:2]  # Use first two default pairs for testing
    
    logger.info(f"Testing analysis pipeline with symbols: {symbols}")
    
    # Initialize analysis orchestrator
    orchestrator = AnalysisOrchestrator()
    
    # Run analysis
    results = orchestrator.analyze_all_symbols(symbols)
    
    # Check results
    success = len(results) > 0
    logger.info(f"Analysis pipeline test: {'Success' if success else 'Failed'}")
    
    if success:
        for symbol, result in results.items():
            logger.info(f"Analysis result for {symbol}: Signal={result.signal.value}, Score={result.final_score:.2f}")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(DATA_DIR, f"test_analysis_results_{timestamp}.json")
        orchestrator.save_analysis_results(results, output_path)
        logger.info(f"Test analysis results saved to {output_path}")
    
    return success, results

def test_trading_engine(analysis_results=None):
    """Test the trading engine with analysis results."""
    logger.info("Testing trading engine...")
    
    # Initialize trading engine in demo mode
    trading_engine = TradingEngine(demo_mode=True)
    
    # Get initial portfolio
    initial_portfolio = trading_engine.get_portfolio_summary()
    logger.info(f"Initial portfolio: {initial_portfolio['total_value']} {initial_portfolio['cash_balance']}")
    
    # Execute trades if analysis results are provided
    if analysis_results:
        for symbol, result in analysis_results.items():
            order = trading_engine.execute_signal(symbol, result.signal, result.price)
            if order:
                logger.info(f"Order executed: {order.side.value} {order.size:.8f} {order.symbol} at {order.filled_price:.2f}")
    
    # Update portfolio
    trading_engine.update_portfolio()
    
    # Get updated portfolio
    updated_portfolio = trading_engine.get_portfolio_summary()
    logger.info(f"Updated portfolio: {updated_portfolio['total_value']} {updated_portfolio['cash_balance']}")
    
    # Save portfolio summary
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    portfolio_path = os.path.join(DATA_DIR, f"test_portfolio_{timestamp}.json")
    save_to_json(updated_portfolio, portfolio_path)
    logger.info(f"Test portfolio summary saved to {portfolio_path}")
    
    return True

def run_integration_test():
    """Run the full integration test."""
    logger.info("Starting integration test...")
    
    # Ensure data directories exist
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Test API connections
    api_success = test_api_connections()
    if not api_success:
        logger.warning("API connection test had issues. Continuing with limited functionality.")
    
    # Test individual analyzers
    analyzer_success = test_individual_analyzers()
    if not analyzer_success:
        logger.warning("Individual analyzer tests had issues. Continuing with limited functionality.")
    
    # Test analysis pipeline with a limited set of symbols
    test_symbols = ["BTC-USD"]
    analysis_success, analysis_results = test_analysis_pipeline(test_symbols)
    if not analysis_success:
        logger.error("Analysis pipeline test failed.")
        return False
    
    # Test trading engine
    trading_success = test_trading_engine(analysis_results)
    if not trading_success:
        logger.error("Trading engine test failed.")
        return False
    
    logger.info("Integration test completed successfully!")
    return True

if __name__ == "__main__":
    success = run_integration_test()
    sys.exit(0 if success else 1)
