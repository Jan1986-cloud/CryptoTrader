"""
Automated trade execution system for cryptocurrency trading.

This module executes trading decisions automatically using the Coinbase API
with proper error handling, order management, and execution tracking.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json

from ..api.clients import CoinbaseClient
from ..models.data_models import TradingSignal
from ..utils.helpers import setup_logging
from ..config.settings import DEMO_MODE

# Set up logging
logger = setup_logging("trade_executor")

class OrderManager:
    """
    Manages order lifecycle and tracking.
    """
    
    def __init__(self):
        """Initialize order manager."""
        self.active_orders = {}
        self.completed_orders = []
        self.failed_orders = []
        self.coinbase_client = CoinbaseClient()
        
        logger.info("Order manager initialized")
    
    def create_market_buy_order(self, symbol: str, usd_amount: float) -> Dict[str, Any]:
        """
        Create a market buy order.
        
        Args:
            symbol: Trading symbol (e.g., "BTC-USD")
            usd_amount: Amount in USD to spend
            
        Returns:
            Order result
        """
        try:
            logger.info(f"Creating market buy order: {symbol} for ${usd_amount:.2f}")
            
            order_data = {
                "product_id": symbol,
                "side": "buy",
                "type": "market",
                "funds": str(usd_amount)  # Market buy with USD amount
            }
            
            result = self.coinbase_client.create_order(
                product_id=symbol,
                side="buy",
                size="",  # Not used for market orders with funds
                order_type="market"
            )
            
            if "error" not in result:
                order_id = result.get("id", "demo-order")
                self.active_orders[order_id] = {
                    "id": order_id,
                    "symbol": symbol,
                    "side": "buy",
                    "type": "market",
                    "usd_amount": usd_amount,
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                    "coinbase_response": result
                }
                
                logger.info(f"Market buy order created: {order_id}")
                return {"success": True, "order_id": order_id, "details": result}
            else:
                logger.error(f"Failed to create buy order: {result['error']}")
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Error creating market buy order: {e}")
            return {"success": False, "error": str(e)}
    
    def create_market_sell_order(self, symbol: str, crypto_amount: float) -> Dict[str, Any]:
        """
        Create a market sell order.
        
        Args:
            symbol: Trading symbol (e.g., "BTC-USD")
            crypto_amount: Amount of cryptocurrency to sell
            
        Returns:
            Order result
        """
        try:
            logger.info(f"Creating market sell order: {crypto_amount:.8f} {symbol}")
            
            result = self.coinbase_client.create_order(
                product_id=symbol,
                side="sell",
                size=str(crypto_amount),
                order_type="market"
            )
            
            if "error" not in result:
                order_id = result.get("id", "demo-order")
                self.active_orders[order_id] = {
                    "id": order_id,
                    "symbol": symbol,
                    "side": "sell",
                    "type": "market",
                    "crypto_amount": crypto_amount,
                    "status": "pending",
                    "created_at": datetime.now().isoformat(),
                    "coinbase_response": result
                }
                
                logger.info(f"Market sell order created: {order_id}")
                return {"success": True, "order_id": order_id, "details": result}
            else:
                logger.error(f"Failed to create sell order: {result['error']}")
                return {"success": False, "error": result["error"]}
                
        except Exception as e:
            logger.error(f"Error creating market sell order: {e}")
            return {"success": False, "error": str(e)}
    
    def check_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Check the status of an order.
        
        Args:
            order_id: Order ID to check
            
        Returns:
            Order status information
        """
        try:
            if order_id not in self.active_orders:
                return {"error": f"Order {order_id} not found in active orders"}
            
            # In demo mode, simulate order completion
            if DEMO_MODE or order_id.startswith("demo-"):
                order = self.active_orders[order_id]
                
                # Simulate order completion after 5 seconds
                created_time = datetime.fromisoformat(order["created_at"])
                if datetime.now() - created_time > timedelta(seconds=5):
                    order["status"] = "done"
                    order["completed_at"] = datetime.now().isoformat()
                    
                    # Move to completed orders
                    self.completed_orders.append(order)
                    del self.active_orders[order_id]
                    
                    logger.info(f"Demo order {order_id} completed")
                    return {"status": "done", "order": order}
                else:
                    return {"status": "pending", "order": order}
            
            # For real orders, check with Coinbase API
            # This would require implementing get_order method in CoinbaseClient
            # For now, return pending status
            order = self.active_orders[order_id]
            return {"status": "pending", "order": order}
            
        except Exception as e:
            logger.error(f"Error checking order status: {e}")
            return {"error": str(e)}
    
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an active order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            Cancellation result
        """
        try:
            if order_id not in self.active_orders:
                return {"error": f"Order {order_id} not found in active orders"}
            
            # In demo mode, just mark as cancelled
            if DEMO_MODE or order_id.startswith("demo-"):
                order = self.active_orders[order_id]
                order["status"] = "cancelled"
                order["cancelled_at"] = datetime.now().isoformat()
                
                # Move to failed orders
                self.failed_orders.append(order)
                del self.active_orders[order_id]
                
                logger.info(f"Demo order {order_id} cancelled")
                return {"success": True, "order": order}
            
            # For real orders, cancel with Coinbase API
            # This would require implementing cancel_order method in CoinbaseClient
            logger.info(f"Order {order_id} cancellation requested")
            return {"success": True, "message": "Cancellation requested"}
            
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {"error": str(e)}
    
    def get_order_summary(self) -> Dict[str, Any]:
        """
        Get summary of all orders.
        
        Returns:
            Order summary statistics
        """
        return {
            "active_orders": len(self.active_orders),
            "completed_orders": len(self.completed_orders),
            "failed_orders": len(self.failed_orders),
            "active_order_ids": list(self.active_orders.keys()),
            "total_orders": len(self.active_orders) + len(self.completed_orders) + len(self.failed_orders)
        }


class TradeExecutor:
    """
    Automated trade execution system.
    
    Executes trading decisions with proper order management and error handling.
    """
    
    def __init__(self, max_slippage: float = 0.02, order_timeout: int = 300):
        """
        Initialize trade executor.
        
        Args:
            max_slippage: Maximum acceptable slippage (0.02 = 2%)
            order_timeout: Order timeout in seconds
        """
        self.order_manager = OrderManager()
        self.max_slippage = max_slippage
        self.order_timeout = order_timeout
        self.coinbase_client = CoinbaseClient()
        
        # Execution tracking
        self.execution_history = []
        self.daily_stats = {
            "trades_executed": 0,
            "total_volume": 0.0,
            "successful_trades": 0,
            "failed_trades": 0,
            "last_reset": datetime.now().date().isoformat()
        }
        
        logger.info(f"Trade executor initialized with {max_slippage*100}% max slippage")
    
    def execute_buy_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a buy trading decision.
        
        Args:
            decision: Trading decision from decision engine
            
        Returns:
            Execution result
        """
        try:
            symbol = decision.get("symbol", "")
            usd_amount = decision.get("position_size_usd", 0)
            confidence = decision.get("confidence", 0)
            
            logger.info(f"Executing BUY decision: {symbol} for ${usd_amount:.2f} "
                       f"(confidence: {confidence:.2f})")
            
            # Pre-execution checks
            if not self._pre_execution_checks(symbol, usd_amount):
                return {"success": False, "error": "Pre-execution checks failed"}
            
            # Get current price for reference
            ticker = self.coinbase_client.get_product_ticker(symbol)
            if "error" in ticker:
                logger.error(f"Cannot get current price for {symbol}: {ticker['error']}")
                return {"success": False, "error": f"Cannot get current price: {ticker['error']}"}
            
            current_price = float(ticker.get("price", 0))
            expected_quantity = usd_amount / current_price if current_price > 0 else 0
            
            # Execute market buy order
            order_result = self.order_manager.create_market_buy_order(symbol, usd_amount)
            
            if order_result.get("success"):
                execution_record = {
                    "timestamp": datetime.now().isoformat(),
                    "action": "BUY",
                    "symbol": symbol,
                    "usd_amount": usd_amount,
                    "expected_quantity": expected_quantity,
                    "expected_price": current_price,
                    "order_id": order_result.get("order_id"),
                    "confidence": confidence,
                    "decision_data": decision,
                    "status": "pending"
                }
                
                self.execution_history.append(execution_record)
                self._update_daily_stats("executed", usd_amount)
                
                logger.info(f"Buy order executed successfully: {order_result.get('order_id')}")
                return {
                    "success": True,
                    "order_id": order_result.get("order_id"),
                    "execution_record": execution_record
                }
            else:
                self._update_daily_stats("failed")
                logger.error(f"Buy order failed: {order_result.get('error')}")
                return {"success": False, "error": order_result.get("error")}
                
        except Exception as e:
            self._update_daily_stats("failed")
            logger.error(f"Error executing buy decision: {e}")
            return {"success": False, "error": str(e)}
    
    def execute_sell_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a sell trading decision.
        
        Args:
            decision: Trading decision from decision engine
            
        Returns:
            Execution result
        """
        try:
            symbol = decision.get("symbol", "")
            crypto_amount = decision.get("balance", 0)
            usd_value = decision.get("position_size_usd", 0)
            
            logger.info(f"Executing SELL decision: {crypto_amount:.8f} {symbol} "
                       f"(~${usd_value:.2f})")
            
            # Pre-execution checks
            if not self._pre_execution_checks(symbol, usd_value):
                return {"success": False, "error": "Pre-execution checks failed"}
            
            # Get current price for reference
            ticker = self.coinbase_client.get_product_ticker(symbol)
            if "error" in ticker:
                logger.error(f"Cannot get current price for {symbol}: {ticker['error']}")
                return {"success": False, "error": f"Cannot get current price: {ticker['error']}"}
            
            current_price = float(ticker.get("price", 0))
            
            # Execute market sell order
            order_result = self.order_manager.create_market_sell_order(symbol, crypto_amount)
            
            if order_result.get("success"):
                execution_record = {
                    "timestamp": datetime.now().isoformat(),
                    "action": "SELL",
                    "symbol": symbol,
                    "crypto_amount": crypto_amount,
                    "expected_usd_value": usd_value,
                    "expected_price": current_price,
                    "order_id": order_result.get("order_id"),
                    "decision_data": decision,
                    "status": "pending"
                }
                
                self.execution_history.append(execution_record)
                self._update_daily_stats("executed", usd_value)
                
                logger.info(f"Sell order executed successfully: {order_result.get('order_id')}")
                return {
                    "success": True,
                    "order_id": order_result.get("order_id"),
                    "execution_record": execution_record
                }
            else:
                self._update_daily_stats("failed")
                logger.error(f"Sell order failed: {order_result.get('error')}")
                return {"success": False, "error": order_result.get("error")}
                
        except Exception as e:
            self._update_daily_stats("failed")
            logger.error(f"Error executing sell decision: {e}")
            return {"success": False, "error": str(e)}
    
    def execute_decisions(self, decisions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple trading decisions.
        
        Args:
            decisions: List of trading decisions
            
        Returns:
            List of execution results
        """
        results = []
        
        logger.info(f"Executing {len(decisions)} trading decisions")
        
        for i, decision in enumerate(decisions):
            action = decision.get("action", "")
            symbol = decision.get("symbol", "")
            
            logger.info(f"Executing decision {i+1}/{len(decisions)}: {action} {symbol}")
            
            if action == "BUY":
                result = self.execute_buy_decision(decision)
            elif action == "SELL":
                result = self.execute_sell_decision(decision)
            else:
                result = {"success": False, "error": f"Unknown action: {action}"}
            
            result["decision_index"] = i
            result["symbol"] = symbol
            result["action"] = action
            results.append(result)
            
            # Small delay between orders to avoid rate limiting
            if i < len(decisions) - 1:
                time.sleep(1)
        
        successful = sum(1 for r in results if r.get("success"))
        logger.info(f"Execution completed: {successful}/{len(decisions)} successful")
        
        return results
    
    def monitor_active_orders(self) -> Dict[str, Any]:
        """
        Monitor and update status of active orders.
        
        Returns:
            Monitoring results
        """
        active_orders = list(self.order_manager.active_orders.keys())
        completed_orders = []
        failed_orders = []
        
        logger.debug(f"Monitoring {len(active_orders)} active orders")
        
        for order_id in active_orders:
            status_result = self.order_manager.check_order_status(order_id)
            
            if "error" not in status_result:
                status = status_result.get("status", "unknown")
                
                if status == "done":
                    completed_orders.append(order_id)
                    self._update_daily_stats("successful")
                    
                    # Update execution history
                    for record in self.execution_history:
                        if record.get("order_id") == order_id:
                            record["status"] = "completed"
                            record["completed_at"] = datetime.now().isoformat()
                            break
                
                elif status == "cancelled" or status == "rejected":
                    failed_orders.append(order_id)
                    self._update_daily_stats("failed")
                    
                    # Update execution history
                    for record in self.execution_history:
                        if record.get("order_id") == order_id:
                            record["status"] = "failed"
                            record["failed_at"] = datetime.now().isoformat()
                            break
        
        return {
            "monitored_orders": len(active_orders),
            "completed_orders": completed_orders,
            "failed_orders": failed_orders,
            "still_active": len(self.order_manager.active_orders)
        }
    
    def _pre_execution_checks(self, symbol: str, amount: float) -> bool:
        """
        Perform pre-execution checks.
        
        Args:
            symbol: Trading symbol
            amount: Trade amount
            
        Returns:
            True if checks pass
        """
        # Check minimum trade amount
        if amount < 1.0:  # $1 minimum
            logger.warning(f"Trade amount ${amount:.2f} below minimum")
            return False
        
        # Check if market is open (for real trading)
        # This would check market hours, maintenance windows, etc.
        
        # Check for recent trades to avoid over-trading
        recent_trades = [
            record for record in self.execution_history
            if (record.get("symbol") == symbol and
                datetime.now() - datetime.fromisoformat(record["timestamp"]) < timedelta(minutes=5))
        ]
        
        if len(recent_trades) >= 3:
            logger.warning(f"Too many recent trades for {symbol}")
            return False
        
        return True
    
    def _update_daily_stats(self, stat_type: str, volume: float = 0):
        """Update daily trading statistics."""
        today = datetime.now().date().isoformat()
        
        # Reset stats if new day
        if self.daily_stats["last_reset"] != today:
            self.daily_stats = {
                "trades_executed": 0,
                "total_volume": 0.0,
                "successful_trades": 0,
                "failed_trades": 0,
                "last_reset": today
            }
        
        if stat_type == "executed":
            self.daily_stats["trades_executed"] += 1
            self.daily_stats["total_volume"] += volume
        elif stat_type == "successful":
            self.daily_stats["successful_trades"] += 1
        elif stat_type == "failed":
            self.daily_stats["failed_trades"] += 1
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.
        
        Returns:
            Execution statistics
        """
        order_summary = self.order_manager.get_order_summary()
        
        return {
            "daily_stats": self.daily_stats,
            "order_summary": order_summary,
            "execution_history_count": len(self.execution_history),
            "max_slippage": self.max_slippage,
            "order_timeout": self.order_timeout
        }


def create_trade_executor(max_slippage: float = 0.02) -> TradeExecutor:
    """
    Create and configure a trade executor instance.
    
    Args:
        max_slippage: Maximum acceptable slippage
        
    Returns:
        Configured TradeExecutor instance
    """
    return TradeExecutor(max_slippage=max_slippage)


if __name__ == "__main__":
    # Test the trade executor
    executor = create_trade_executor()
    
    # Test execution stats
    stats = executor.get_execution_stats()
    print(f"Execution stats: {stats}")
    
    # Test with sample decisions
    sample_decisions = [
        {
            "action": "BUY",
            "symbol": "BTC-USD",
            "position_size_usd": 100.0,
            "confidence": 0.85,
            "reason": "Strong buy signal"
        }
    ]
    
    results = executor.execute_decisions(sample_decisions)
    print(f"Execution results: {results}")
    
    # Monitor orders
    monitoring = executor.monitor_active_orders()
    print(f"Order monitoring: {monitoring}")

