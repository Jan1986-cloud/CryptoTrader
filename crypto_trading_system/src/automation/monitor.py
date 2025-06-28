"""
Real-time monitoring system for cryptocurrency trading.

This module continuously monitors all tradeable cryptocurrencies and identifies
trading opportunities based on comprehensive analysis.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import threading

from ..api.clients import CoinbaseClient
from ..analysis.orchestrator import AnalysisOrchestrator
from ..models.data_models import TradingSignal
from ..utils.helpers import setup_logging
from ..config.settings import DEMO_MODE

# Set up logging
logger = setup_logging("crypto_monitor")

class CryptoMonitor:
    """
    Real-time cryptocurrency monitoring system.
    
    Continuously monitors all tradeable coins and identifies trading opportunities.
    """
    
    def __init__(self, update_interval: int = 3600):  # Default 1 hour
        """
        Initialize the crypto monitor.
        
        Args:
            update_interval: Interval in seconds between analysis updates
        """
        self.coinbase_client = CoinbaseClient()
        self.orchestrator = AnalysisOrchestrator()
        self.update_interval = update_interval
        self.is_running = False
        self.tradeable_coins = []
        self.last_analysis = {}
        self.monitoring_thread = None
        
        # Portfolio settings
        self.max_position_percentage = 0.1  # 10% max per position
        self.total_portfolio_percentage = 0.8  # 80% max invested
        
        logger.info(f"CryptoMonitor initialized with {update_interval}s interval")
    
    def get_tradeable_coins(self) -> List[str]:
        """
        Get all tradeable cryptocurrency pairs from Coinbase.
        
        Returns:
            List of tradeable coin symbols
        """
        try:
            products = self.coinbase_client.get_products()
            
            if "error" in products:
                logger.error(f"Error fetching products: {products['error']}")
                return []
            
            # Extract USD trading pairs
            tradeable = []
            if "products" in products:
                for product in products["products"]:
                    product_id = product.get("product_id", "")
                    status = product.get("status", "")
                    
                    # Only include active USD pairs
                    if product_id.endswith("-USD") and status == "online":
                        tradeable.append(product_id)
            
            logger.info(f"Found {len(tradeable)} tradeable coins")
            return sorted(tradeable)
            
        except Exception as e:
            logger.error(f"Error getting tradeable coins: {e}")
            return []
    
    def analyze_coin(self, symbol: str, timeframe: str = "1h") -> Optional[Dict[str, Any]]:
        """
        Analyze a single cryptocurrency for trading opportunities.
        
        Args:
            symbol: Trading symbol (e.g., "BTC-USD")
            timeframe: Analysis timeframe
            
        Returns:
            Analysis result or None if failed
        """
        try:
            logger.debug(f"Analyzing {symbol} with {timeframe} timeframe")
            
            # Perform comprehensive analysis
            result = self.orchestrator.analyze_symbol(symbol, timeframe)
            
            if result and hasattr(result, 'signal'):
                analysis_data = {
                    "symbol": symbol,
                    "timestamp": datetime.now().isoformat(),
                    "timeframe": timeframe,
                    "signal": result.signal,
                    "confidence": result.confidence,
                    "data": result.data if hasattr(result, 'data') else {}
                }
                
                logger.debug(f"Analysis complete for {symbol}: {result.signal}")
                return analysis_data
            
            logger.warning(f"No valid analysis result for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def analyze_all_coins(self, timeframe: str = "1h") -> Dict[str, Any]:
        """
        Analyze all tradeable coins in parallel.
        
        Args:
            timeframe: Analysis timeframe
            
        Returns:
            Dictionary of analysis results
        """
        logger.info(f"Starting analysis of {len(self.tradeable_coins)} coins")
        start_time = time.time()
        
        results = {}
        
        # Use ThreadPoolExecutor for parallel analysis
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all analysis tasks
            future_to_symbol = {
                executor.submit(self.analyze_coin, symbol, timeframe): symbol
                for symbol in self.tradeable_coins
            }
            
            # Collect results
            for future in future_to_symbol:
                symbol = future_to_symbol[future]
                try:
                    result = future.result(timeout=60)  # 60 second timeout per coin
                    if result:
                        results[symbol] = result
                except Exception as e:
                    logger.error(f"Error analyzing {symbol}: {e}")
        
        elapsed_time = time.time() - start_time
        logger.info(f"Analysis completed in {elapsed_time:.2f}s. {len(results)} successful analyses")
        
        return results
    
    def identify_best_opportunities(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify the best trading opportunities from analysis results.
        
        Args:
            analysis_results: Results from analyze_all_coins
            
        Returns:
            List of best opportunities sorted by potential return
        """
        opportunities = []
        
        for symbol, result in analysis_results.items():
            signal = result.get("signal", "NEUTRAL")
            confidence = result.get("confidence", 0)
            
            # Only consider strong signals with high confidence
            if signal in ["BUY", "STRONG_BUY"] and confidence > 0.7:
                opportunity = {
                    "symbol": symbol,
                    "signal": signal,
                    "confidence": confidence,
                    "potential_return": confidence * (2 if signal == "STRONG_BUY" else 1),
                    "timestamp": result.get("timestamp"),
                    "analysis_data": result
                }
                opportunities.append(opportunity)
        
        # Sort by potential return (descending)
        opportunities.sort(key=lambda x: x["potential_return"], reverse=True)
        
        logger.info(f"Identified {len(opportunities)} trading opportunities")
        return opportunities
    
    def calculate_position_size(self, symbol: str, portfolio_value: float) -> float:
        """
        Calculate optimal position size based on portfolio percentage.
        
        Args:
            symbol: Trading symbol
            portfolio_value: Total portfolio value in USD
            
        Returns:
            Position size in USD
        """
        max_position_value = portfolio_value * self.max_position_percentage
        
        # Additional risk-based adjustments could be added here
        # For now, use the maximum allowed percentage
        
        logger.debug(f"Position size for {symbol}: ${max_position_value:.2f}")
        return max_position_value
    
    def monitoring_loop(self):
        """
        Main monitoring loop that runs continuously.
        """
        logger.info("Starting monitoring loop")
        
        while self.is_running:
            try:
                loop_start = time.time()
                
                # Get current tradeable coins (refresh periodically)
                self.tradeable_coins = self.get_tradeable_coins()
                
                if not self.tradeable_coins:
                    logger.warning("No tradeable coins found, retrying in 5 minutes")
                    time.sleep(300)  # Wait 5 minutes before retry
                    continue
                
                # Analyze all coins for different timeframes
                timeframes = ["1h", "1d", "7d"]
                all_results = {}
                
                for timeframe in timeframes:
                    logger.info(f"Analyzing all coins for {timeframe} timeframe")
                    results = self.analyze_all_coins(timeframe)
                    all_results[timeframe] = results
                
                # Store results
                self.last_analysis = {
                    "timestamp": datetime.now().isoformat(),
                    "results": all_results
                }
                
                # Identify best opportunities across all timeframes
                best_opportunities = []
                for timeframe, results in all_results.items():
                    opportunities = self.identify_best_opportunities(results)
                    for opp in opportunities:
                        opp["timeframe"] = timeframe
                        best_opportunities.append(opp)
                
                # Sort all opportunities by potential return
                best_opportunities.sort(key=lambda x: x["potential_return"], reverse=True)
                
                # Log top opportunities
                if best_opportunities:
                    logger.info("Top trading opportunities:")
                    for i, opp in enumerate(best_opportunities[:5]):
                        logger.info(f"  {i+1}. {opp['symbol']} ({opp['timeframe']}) - "
                                  f"{opp['signal']} (confidence: {opp['confidence']:.2f})")
                
                # Calculate sleep time to maintain interval
                loop_duration = time.time() - loop_start
                sleep_time = max(0, self.update_interval - loop_duration)
                
                logger.info(f"Monitoring cycle completed in {loop_duration:.2f}s. "
                          f"Sleeping for {sleep_time:.2f}s")
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry
    
    def start_monitoring(self):
        """Start the monitoring system."""
        if self.is_running:
            logger.warning("Monitoring is already running")
            return
        
        self.is_running = True
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("Crypto monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring system."""
        if not self.is_running:
            logger.warning("Monitoring is not running")
            return
        
        self.is_running = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        logger.info("Crypto monitoring stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current monitoring status.
        
        Returns:
            Status information
        """
        return {
            "is_running": self.is_running,
            "update_interval": self.update_interval,
            "tradeable_coins_count": len(self.tradeable_coins),
            "last_analysis_time": self.last_analysis.get("timestamp"),
            "max_position_percentage": self.max_position_percentage,
            "total_portfolio_percentage": self.total_portfolio_percentage
        }
    
    def get_latest_opportunities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the latest trading opportunities.
        
        Args:
            limit: Maximum number of opportunities to return
            
        Returns:
            List of trading opportunities
        """
        if not self.last_analysis or "results" not in self.last_analysis:
            return []
        
        all_opportunities = []
        
        for timeframe, results in self.last_analysis["results"].items():
            opportunities = self.identify_best_opportunities(results)
            for opp in opportunities:
                opp["timeframe"] = timeframe
                all_opportunities.append(opp)
        
        # Sort by potential return and return top opportunities
        all_opportunities.sort(key=lambda x: x["potential_return"], reverse=True)
        return all_opportunities[:limit]


def create_monitor(update_interval: int = 3600) -> CryptoMonitor:
    """
    Create and configure a crypto monitor instance.
    
    Args:
        update_interval: Update interval in seconds
        
    Returns:
        Configured CryptoMonitor instance
    """
    return CryptoMonitor(update_interval=update_interval)


if __name__ == "__main__":
    # Test the monitoring system
    monitor = create_monitor(update_interval=300)  # 5 minutes for testing
    
    try:
        monitor.start_monitoring()
        
        # Run for a short time for testing
        time.sleep(60)
        
        # Check status
        status = monitor.get_status()
        print(f"Monitor status: {status}")
        
        # Get opportunities
        opportunities = monitor.get_latest_opportunities(5)
        print(f"Latest opportunities: {opportunities}")
        
    finally:
        monitor.stop_monitoring()

