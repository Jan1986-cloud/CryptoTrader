"""
Main automation orchestrator for cryptocurrency trading.

This module coordinates all automation components to provide a complete
automated trading system with monitoring, decision making, execution,
and risk management.
"""

import asyncio
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

from .monitor import CryptoMonitor
from .decision_engine import AutomatedDecisionEngine
from .trade_executor import TradeExecutor
from .risk_manager import RiskManager
from ..utils.helpers import setup_logging
from ..config.settings import DEMO_MODE

# Set up logging
logger = setup_logging("auto_trader")

class AutomatedTrader:
    """
    Complete automated cryptocurrency trading system.
    
    Coordinates monitoring, analysis, decision making, execution, and risk management.
    """
    
    def __init__(self, 
                 update_interval: int = 3600,  # 1 hour
                 max_position_percentage: float = 0.1,  # 10%
                 max_total_invested: float = 0.8,  # 80%
                 min_confidence: float = 0.75):
        """
        Initialize the automated trader.
        
        Args:
            update_interval: Analysis interval in seconds
            max_position_percentage: Maximum percentage per position
            max_total_invested: Maximum total portfolio percentage invested
            min_confidence: Minimum confidence for trades
        """
        self.update_interval = update_interval
        self.is_running = False
        self.trading_enabled = True
        
        # Initialize components
        self.monitor = CryptoMonitor(update_interval=update_interval)
        self.decision_engine = AutomatedDecisionEngine(
            max_position_percentage=max_position_percentage,
            max_total_invested=max_total_invested,
            min_confidence=min_confidence
        )
        self.trade_executor = TradeExecutor()
        self.risk_manager = RiskManager(
            max_position_risk=max_position_percentage,
            max_portfolio_risk=0.02  # 2% daily portfolio risk
        )
        
        # Trading state
        self.trading_thread = None
        self.last_trading_cycle = None
        self.trading_stats = {
            "cycles_completed": 0,
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_volume": 0.0,
            "start_time": None
        }
        
        logger.info(f"Automated trader initialized with {update_interval}s interval")
    
    def start_trading(self):
        """Start the automated trading system."""
        if self.is_running:
            logger.warning("Automated trading is already running")
            return
        
        self.is_running = True
        self.trading_stats["start_time"] = datetime.now().isoformat()
        
        # Start monitoring
        self.monitor.start_monitoring()
        
        # Start trading loop
        self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
        self.trading_thread.start()
        
        logger.info("Automated trading system started")
    
    def stop_trading(self):
        """Stop the automated trading system."""
        if not self.is_running:
            logger.warning("Automated trading is not running")
            return
        
        self.is_running = False
        
        # Stop monitoring
        self.monitor.stop_monitoring()
        
        # Wait for trading thread to finish
        if self.trading_thread:
            self.trading_thread.join(timeout=30)
        
        logger.info("Automated trading system stopped")
    
    def enable_trading(self):
        """Enable trade execution."""
        self.trading_enabled = True
        logger.info("Trade execution enabled")
    
    def disable_trading(self):
        """Disable trade execution (monitoring continues)."""
        self.trading_enabled = False
        logger.info("Trade execution disabled")
    
    def _trading_loop(self):
        """Main trading loop that runs continuously."""
        logger.info("Starting automated trading loop")
        
        while self.is_running:
            try:
                cycle_start = time.time()
                
                logger.info("Starting trading cycle")
                
                # Get latest opportunities from monitor
                opportunities = self.monitor.get_latest_opportunities(limit=20)
                
                if not opportunities:
                    logger.info("No trading opportunities found")
                    self._sleep_until_next_cycle(cycle_start)
                    continue
                
                logger.info(f"Found {len(opportunities)} trading opportunities")
                
                # Get current portfolio state
                portfolio = self.decision_engine.portfolio_manager.get_portfolio_value()
                
                if "error" in portfolio:
                    logger.error(f"Portfolio error: {portfolio['error']}")
                    self._sleep_until_next_cycle(cycle_start)
                    continue
                
                # Monitor portfolio risk
                risk_status = self.risk_manager.monitor_portfolio_risk(portfolio)
                
                # Check for critical risk alerts
                critical_alerts = [
                    alert for alert in risk_status.get("risk_alerts", [])
                    if alert.get("severity") == "critical"
                ]
                
                if critical_alerts:
                    logger.warning(f"Critical risk alerts detected: {critical_alerts}")
                    logger.warning("Skipping trading cycle due to risk concerns")
                    self._sleep_until_next_cycle(cycle_start)
                    continue
                
                # Make trading decisions
                decisions = self.decision_engine.make_trading_decision(opportunities)
                
                if not decisions:
                    logger.info("No trading decisions generated")
                    self._sleep_until_next_cycle(cycle_start)
                    continue
                
                logger.info(f"Generated {len(decisions)} trading decisions")
                
                # Risk assessment for each decision
                approved_decisions = []
                for decision in decisions:
                    risk_assessment = self.risk_manager.assess_trade_risk(decision, portfolio)
                    
                    if risk_assessment.get("approved", False):
                        # Apply any risk adjustments
                        adjustments = risk_assessment.get("adjustments", {})
                        for key, value in adjustments.items():
                            decision[key] = value
                        
                        approved_decisions.append(decision)
                        logger.info(f"Decision approved: {decision['action']} {decision['symbol']}")
                    else:
                        logger.warning(f"Decision rejected by risk manager: {decision['symbol']}")
                        logger.warning(f"Risk warnings: {risk_assessment.get('warnings', [])}")
                
                if not approved_decisions:
                    logger.info("No decisions approved by risk manager")
                    self._sleep_until_next_cycle(cycle_start)
                    continue
                
                # Execute approved decisions (if trading is enabled)
                if self.trading_enabled:
                    logger.info(f"Executing {len(approved_decisions)} approved decisions")
                    
                    execution_results = self.trade_executor.execute_decisions(approved_decisions)
                    
                    # Process execution results
                    successful_executions = 0
                    failed_executions = 0
                    total_volume = 0.0
                    
                    for result in execution_results:
                        if result.get("success"):
                            successful_executions += 1
                            # Set stop-losses for new positions
                            if result.get("action") == "BUY":
                                symbol = result.get("symbol")
                                # Get entry price from execution
                                # For now, use current market price
                                ticker = self.monitor.coinbase_client.get_product_ticker(symbol)
                                if "price" in ticker:
                                    entry_price = float(ticker["price"])
                                    self.risk_manager.stop_loss_manager.set_stop_loss(
                                        symbol, entry_price
                                    )
                        else:
                            failed_executions += 1
                        
                        # Track volume
                        if "position_size_usd" in result:
                            total_volume += result.get("position_size_usd", 0)
                    
                    # Update trading stats
                    self.trading_stats["cycles_completed"] += 1
                    self.trading_stats["total_trades"] += len(execution_results)
                    self.trading_stats["successful_trades"] += successful_executions
                    self.trading_stats["failed_trades"] += failed_executions
                    self.trading_stats["total_volume"] += total_volume
                    
                    logger.info(f"Execution completed: {successful_executions} successful, "
                              f"{failed_executions} failed, ${total_volume:.2f} volume")
                else:
                    logger.info("Trading disabled - decisions not executed")
                
                # Monitor active orders
                order_monitoring = self.trade_executor.monitor_active_orders()
                logger.debug(f"Order monitoring: {order_monitoring}")
                
                # Check stop-loss triggers
                current_prices = {}
                for opportunity in opportunities:
                    symbol = opportunity.get("symbol")
                    if symbol:
                        ticker = self.monitor.coinbase_client.get_product_ticker(symbol)
                        if "price" in ticker:
                            current_prices[symbol] = float(ticker["price"])
                
                triggered_stops = self.risk_manager.stop_loss_manager.check_stop_triggers(current_prices)
                
                if triggered_stops:
                    logger.warning(f"{len(triggered_stops)} stop-losses triggered")
                    
                    # Execute stop-loss sells if trading is enabled
                    if self.trading_enabled:
                        for stop in triggered_stops:
                            symbol = stop["symbol"]
                            # Create sell decision for stop-loss
                            stop_decision = {
                                "action": "SELL",
                                "symbol": symbol,
                                "reason": "Stop-loss triggered",
                                "trigger_price": stop["trigger_price"]
                            }
                            
                            # Get current position size
                            portfolio = self.decision_engine.portfolio_manager.get_portfolio_value()
                            positions = portfolio.get("positions", {})
                            currency = symbol.split("-")[0]
                            
                            if currency in positions:
                                stop_decision["balance"] = positions[currency]["balance"]
                                stop_decision["position_size_usd"] = positions[currency]["value_usd"]
                                
                                # Execute stop-loss sell
                                stop_result = self.trade_executor.execute_sell_decision(stop_decision)
                                
                                if stop_result.get("success"):
                                    logger.info(f"Stop-loss executed for {symbol}")
                                    # Remove stop-loss after execution
                                    self.risk_manager.stop_loss_manager.remove_stop_loss(symbol)
                                else:
                                    logger.error(f"Failed to execute stop-loss for {symbol}")
                
                self.last_trading_cycle = datetime.now().isoformat()
                
                # Sleep until next cycle
                self._sleep_until_next_cycle(cycle_start)
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                time.sleep(60)  # Wait 1 minute before retry
    
    def _sleep_until_next_cycle(self, cycle_start: float):
        """Sleep until the next trading cycle."""
        cycle_duration = time.time() - cycle_start
        sleep_time = max(0, self.update_interval - cycle_duration)
        
        logger.info(f"Trading cycle completed in {cycle_duration:.2f}s. "
                   f"Sleeping for {sleep_time:.2f}s")
        
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status of the automated trading system.
        
        Returns:
            System status information
        """
        monitor_status = self.monitor.get_status()
        decision_stats = self.decision_engine.get_decision_stats()
        execution_stats = self.trade_executor.get_execution_stats()
        risk_summary = self.risk_manager.get_risk_summary()
        
        return {
            "is_running": self.is_running,
            "trading_enabled": self.trading_enabled,
            "last_trading_cycle": self.last_trading_cycle,
            "trading_stats": self.trading_stats,
            "monitor_status": monitor_status,
            "decision_stats": decision_stats,
            "execution_stats": execution_stats,
            "risk_summary": risk_summary,
            "update_interval": self.update_interval
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary of the trading system.
        
        Returns:
            Performance metrics
        """
        stats = self.trading_stats
        
        # Calculate success rate
        total_trades = stats["total_trades"]
        success_rate = (stats["successful_trades"] / total_trades * 100) if total_trades > 0 else 0
        
        # Calculate average trade size
        avg_trade_size = (stats["total_volume"] / total_trades) if total_trades > 0 else 0
        
        # Calculate uptime
        start_time = stats.get("start_time")
        uptime_hours = 0
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            uptime_hours = (datetime.now() - start_dt).total_seconds() / 3600
        
        return {
            "uptime_hours": uptime_hours,
            "cycles_completed": stats["cycles_completed"],
            "total_trades": total_trades,
            "success_rate": success_rate,
            "total_volume": stats["total_volume"],
            "average_trade_size": avg_trade_size,
            "trades_per_hour": total_trades / uptime_hours if uptime_hours > 0 else 0
        }
    
    def emergency_stop(self):
        """Emergency stop - immediately halt all trading and cancel orders."""
        logger.warning("EMERGENCY STOP ACTIVATED")
        
        # Disable trading
        self.trading_enabled = False
        
        # Cancel all active orders
        active_orders = list(self.trade_executor.order_manager.active_orders.keys())
        for order_id in active_orders:
            try:
                self.trade_executor.order_manager.cancel_order(order_id)
                logger.info(f"Emergency cancelled order: {order_id}")
            except Exception as e:
                logger.error(f"Failed to cancel order {order_id}: {e}")
        
        # Stop the system
        self.stop_trading()
        
        logger.warning("Emergency stop completed")


def create_automated_trader(update_interval: int = 3600,
                           max_position_percentage: float = 0.1,
                           max_total_invested: float = 0.8) -> AutomatedTrader:
    """
    Create and configure an automated trader instance.
    
    Args:
        update_interval: Analysis interval in seconds
        max_position_percentage: Maximum percentage per position
        max_total_invested: Maximum total portfolio percentage invested
        
    Returns:
        Configured AutomatedTrader instance
    """
    return AutomatedTrader(
        update_interval=update_interval,
        max_position_percentage=max_position_percentage,
        max_total_invested=max_total_invested
    )


if __name__ == "__main__":
    # Test the automated trader
    trader = create_automated_trader(update_interval=300)  # 5 minutes for testing
    
    try:
        # Start trading
        trader.start_trading()
        
        # Run for a short time for testing
        time.sleep(60)
        
        # Check status
        status = trader.get_status()
        print(f"Trader status: {json.dumps(status, indent=2)}")
        
        # Check performance
        performance = trader.get_performance_summary()
        print(f"Performance: {json.dumps(performance, indent=2)}")
        
    finally:
        trader.stop_trading()

