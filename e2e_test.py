#!/usr/bin/env python3

"""
End-to-end test script for the Cryptocurrency Trading System.

This script tests the entire system from data collection to trading execution,
verifying that all components work together correctly.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.append(os.path.join(os.path.dirname(__file__)))

from crypto_trading_system.crypto_trading_system.src.utils.helpers import setup_logging
from crypto_trading_system.crypto_trading_system.src.api.clients import CoinbaseClient
from crypto_trading_system.crypto_trading_system.src.analysis.orchestrator import AnalysisOrchestrator
from crypto_trading_system.crypto_trading_system.src.trading.engine import execute_trade_strategy

# Set up logging
logger = setup_logging("e2e_test")

def test_data_collection(symbols, interval="1h"):
    """Test data collection for multiple cryptocurrencies."""
    logger.info(f"Testing data collection for {len(symbols)} symbols with interval {interval}")
    
    client = CoinbaseClient()
    
    success_count = 0
    for symbol in symbols:
        try:
            # Get candles
            candles = client.get_candles(symbol, granularity=3600 if interval == "1h" else 86400)
            
            if isinstance(candles, list) and len(candles) > 0:
                logger.info(f"Successfully fetched {len(candles)} candles for {symbol}")
                success_count += 1
            else:
                logger.error(f"Failed to fetch candles for {symbol}")
        
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
    
    success_rate = success_count / len(symbols) if symbols else 0
    logger.info(f"Data collection test completed with {success_rate:.0%} success rate")
    
    return success_rate >= 0.8  # At least 80% success rate

def test_analysis_pipeline(symbols, interval="1h"):
    """Test the analysis pipeline for multiple cryptocurrencies."""
    logger.info(f"Testing analysis pipeline for {len(symbols)} symbols with interval {interval}")
    
    success_count = 0
    results = {}
    
    # Create orchestrator instance
    orchestrator = AnalysisOrchestrator()
    
    for symbol in symbols:
        try:
            # Analyze cryptocurrency
            analysis_result = orchestrator.analyze_symbol(symbol)
            
            if analysis_result and hasattr(analysis_result, 'signal'):
                logger.info(f"Successfully analyzed {symbol}: {analysis_result.signal}")
                results[symbol] = analysis_result
                success_count += 1
            else:
                logger.error(f"Failed to analyze {symbol}")
        
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
    
    # Save analysis results
    if results:
        orchestrator.save_analysis_results(results, "e2e_test_results.json")
    
    success_rate = success_count / len(symbols) if symbols else 0
    logger.info(f"Analysis pipeline test completed with {success_rate:.0%} success rate")
    
    return success_rate >= 0.8  # At least 80% success rate

def test_trading_engine(symbols, interval="1h", execute=False):
    """Test the trading engine for multiple cryptocurrencies."""
    logger.info(f"Testing trading engine for {len(symbols)} symbols with interval {interval}")
    
    client = CoinbaseClient()
    orchestrator = AnalysisOrchestrator()
    
    success_count = 0
    for symbol in symbols:
        try:
            # Analyze cryptocurrency
            analysis_result = orchestrator.analyze_symbol(symbol)
            
            if not analysis_result or not hasattr(analysis_result, 'signal'):
                logger.error(f"Failed to analyze {symbol} for trading")
                continue
            
            # Execute trade strategy (in demo mode)
            trade_result = execute_trade_strategy(
                symbol=symbol,
                signal=analysis_result.signal,
                client=client,
                execute=execute
            )
            
            if trade_result and "status" in trade_result:
                logger.info(f"Successfully tested trading for {symbol}: {trade_result['status']}")
                success_count += 1
            else:
                logger.error(f"Failed to test trading for {symbol}")
        
        except Exception as e:
            logger.error(f"Error testing trading for {symbol}: {e}")
    
    success_rate = success_count / len(symbols) if symbols else 0
    logger.info(f"Trading engine test completed with {success_rate:.0%} success rate")
    
    return success_rate >= 0.8  # At least 80% success rate

def test_ui_data_integration():
    """Test the integration between UI and data pipeline."""
    logger.info("Testing UI data integration")
    
    try:
        # Generate test data for UI
        symbols = ["BTC-USD", "ETH-USD", "SOL-USD"]
        
        # Create orchestrator instance
        orchestrator = AnalysisOrchestrator()
        
        # Analyze symbols
        results = {}
        for symbol in symbols:
            analysis_result = orchestrator.analyze_symbol(symbol)
            if analysis_result:
                results[symbol] = analysis_result
        
        # Save results for UI to consume
        orchestrator.save_analysis_results(results, "ui_test_data.json")
        
        # Check if file was created
        if os.path.exists("ui_test_data.json"):
            with open("ui_test_data.json", "r") as f:
                data = json.load(f)
                if len(data) == len(symbols):
                    logger.info("Successfully generated UI test data")
                    return True
        
        logger.error("Failed to generate UI test data")
        return False
    
    except Exception as e:
        logger.error(f"Error testing UI data integration: {e}")
        return False

def run_all_tests(symbols=None, interval="1h", execute_trades=False):
    """Run all end-to-end tests."""
    if symbols is None:
        symbols = ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "XRP-USD"]
    
    logger.info(f"Running all end-to-end tests with interval {interval}")
    
    # Test data collection
    data_collection_success = test_data_collection(symbols, interval)
    logger.info(f"Data collection test: {'PASSED' if data_collection_success else 'FAILED'}")
    
    # Test analysis pipeline
    analysis_pipeline_success = test_analysis_pipeline(symbols, interval)
    logger.info(f"Analysis pipeline test: {'PASSED' if analysis_pipeline_success else 'FAILED'}")
    
    # Test trading engine
    trading_engine_success = test_trading_engine(symbols, interval, execute_trades)
    logger.info(f"Trading engine test: {'PASSED' if trading_engine_success else 'FAILED'}")
    
    # Test UI data integration
    ui_integration_success = test_ui_data_integration()
    logger.info(f"UI data integration test: {'PASSED' if ui_integration_success else 'FAILED'}")
    
    # Overall success
    overall_success = all([
        data_collection_success,
        analysis_pipeline_success,
        trading_engine_success,
        ui_integration_success
    ])
    
    logger.info(f"End-to-end tests: {'PASSED' if overall_success else 'FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run end-to-end tests for the Cryptocurrency Trading System")
    parser.add_argument("--symbols", nargs="+", help="Symbols to test")
    parser.add_argument("--interval", default="1h", choices=["1h", "1d", "7d", "30d", "90d"], help="Time interval")
    parser.add_argument("--execute", action="store_true", help="Execute trades (in demo mode)")
    
    args = parser.parse_args()
    
    success = run_all_tests(args.symbols, args.interval, args.execute)
    sys.exit(0 if success else 1)
