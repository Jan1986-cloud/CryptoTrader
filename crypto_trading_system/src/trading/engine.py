"""
Trading engine module for the Cryptocurrency Trading System.

This module provides functionality for executing trades based on analysis results.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from ..utils.helpers import setup_logging
from ..api.clients import CoinbaseClient
from ..models.data_models import TradingSignal

# Set up logging
logger = setup_logging("trading_engine")

def execute_trade_strategy(symbol: str, signal: TradingSignal, client: CoinbaseClient = None, execute: bool = False) -> Dict[str, Any]:
    """
    Execute a trading strategy based on analysis signal.
    
    Args:
        symbol: Trading symbol (e.g., 'BTC-USD')
        signal: Trading signal from analysis
        client: CoinbaseClient instance (creates new one if None)
        execute: Whether to actually execute trades or just simulate
        
    Returns:
        Dictionary with trade execution results
    """
    logger.info(f"Executing trade strategy for {symbol} with signal {signal}")
    
    # Create client if not provided
    if client is None:
        client = CoinbaseClient()
    
    # Initialize result
    result = {
        "symbol": symbol,
        "signal": signal.value if hasattr(signal, 'value') else str(signal),
        "timestamp": datetime.now().isoformat(),
        "status": "SIMULATED",  # Default to simulated
        "action": "NONE",
        "price": None,
        "quantity": None,
        "total": None,
        "order_id": None,
        "error": None
    }
    
    try:
        # Get current price
        product_data = client.get_product(symbol)
        if "error" in product_data:
            result["error"] = f"Error getting product data: {product_data['error']}"
            logger.error(result["error"])
            return result
        
        current_price = float(product_data.get("price", 0))
        result["price"] = current_price
        
        # Determine action based on signal
        if signal == TradingSignal.STRONG_BUY or signal == TradingSignal.BUY:
            result["action"] = "BUY"
        elif signal == TradingSignal.STRONG_SELL or signal == TradingSignal.SELL:
            result["action"] = "SELL"
        else:
            result["action"] = "HOLD"
            logger.info(f"Signal {signal} for {symbol} indicates HOLD, no trade executed")
            return result
        
        # If just simulating, return result
        if not execute:
            logger.info(f"Simulated {result['action']} for {symbol} at {current_price}")
            return result
        
        # Get account balances
        accounts = client.get_accounts()
        if "error" in accounts:
            result["error"] = f"Error getting accounts: {accounts['error']}"
            logger.error(result["error"])
            return result
        
        # Extract base and quote currencies from symbol
        base_currency, quote_currency = symbol.split("-")
        
        # Find relevant accounts
        base_account = None
        quote_account = None
        
        for account in accounts.get("accounts", []):
            if account["currency"] == base_currency:
                base_account = account
            elif account["currency"] == quote_currency:
                quote_account = account
        
        if not base_account or not quote_account:
            result["error"] = f"Could not find accounts for {base_currency} or {quote_currency}"
            logger.error(result["error"])
            return result
        
        # Calculate trade size based on account balance and risk settings
        if result["action"] == "BUY":
            # Use 5% of quote currency balance for buy
            available_balance = float(quote_account["available"])
            trade_amount = available_balance * 0.05
            quantity = trade_amount / current_price
            
            # Execute buy order
            order = client.create_order(
                product_id=symbol,
                side="buy",
                size=str(quantity),
                price=str(current_price)
            )
            
            if "error" in order:
                result["error"] = f"Error creating buy order: {order['error']}"
                logger.error(result["error"])
                return result
            
            result["quantity"] = quantity
            result["total"] = trade_amount
            result["order_id"] = order.get("id")
            result["status"] = "EXECUTED"
            
            logger.info(f"Executed BUY for {quantity} {base_currency} at {current_price} {quote_currency}")
        
        elif result["action"] == "SELL":
            # Use 10% of base currency balance for sell
            available_balance = float(base_account["available"])
            quantity = available_balance * 0.1
            trade_amount = quantity * current_price
            
            # Execute sell order
            order = client.create_order(
                product_id=symbol,
                side="sell",
                size=str(quantity),
                price=str(current_price)
            )
            
            if "error" in order:
                result["error"] = f"Error creating sell order: {order['error']}"
                logger.error(result["error"])
                return result
            
            result["quantity"] = quantity
            result["total"] = trade_amount
            result["order_id"] = order.get("id")
            result["status"] = "EXECUTED"
            
            logger.info(f"Executed SELL for {quantity} {base_currency} at {current_price} {quote_currency}")
    
    except Exception as e:
        result["error"] = f"Error executing trade strategy: {e}"
        logger.error(result["error"])
    
    return result

def get_portfolio_status(client: CoinbaseClient = None) -> Dict[str, Any]:
    """
    Get current portfolio status.
    
    Args:
        client: CoinbaseClient instance (creates new one if None)
        
    Returns:
        Dictionary with portfolio status
    """
    logger.info("Getting portfolio status")
    
    # Create client if not provided
    if client is None:
        client = CoinbaseClient()
    
    # Initialize result
    result = {
        "timestamp": datetime.now().isoformat(),
        "total_value_usd": 0.0,
        "assets": [],
        "error": None
    }
    
    try:
        # Get accounts
        accounts = client.get_accounts()
        if "error" in accounts:
            result["error"] = f"Error getting accounts: {accounts['error']}"
            logger.error(result["error"])
            return result
        
        # Process accounts
        for account in accounts.get("accounts", []):
            currency = account["currency"]
            balance = float(account["balance"])
            
            if balance > 0:
                # Get USD value for non-USD currencies
                usd_value = balance
                if currency != "USD":
                    # Get product data for currency-USD pair
                    product_data = client.get_product(f"{currency}-USD")
                    if "error" not in product_data:
                        price = float(product_data.get("price", 0))
                        usd_value = balance * price
                
                # Add to total value
                result["total_value_usd"] += usd_value
                
                # Add asset to list
                result["assets"].append({
                    "currency": currency,
                    "balance": balance,
                    "usd_value": usd_value
                })
        
        logger.info(f"Portfolio total value: ${result['total_value_usd']:.2f}")
    
    except Exception as e:
        result["error"] = f"Error getting portfolio status: {e}"
        logger.error(result["error"])
    
    return result

def get_trade_history(client: CoinbaseClient = None) -> Dict[str, Any]:
    """
    Get trade history.
    
    Args:
        client: CoinbaseClient instance (creates new one if None)
        
    Returns:
        Dictionary with trade history
    """
    logger.info("Getting trade history")
    
    # Create client if not provided
    if client is None:
        client = CoinbaseClient()
    
    # Initialize result
    result = {
        "timestamp": datetime.now().isoformat(),
        "trades": [],
        "error": None
    }
    
    try:
        # Get orders
        orders = client.get_orders()
        if "error" in orders:
            result["error"] = f"Error getting orders: {orders['error']}"
            logger.error(result["error"])
            return result
        
        # Process orders
        for order in orders.get("orders", []):
            result["trades"].append({
                "id": order.get("id"),
                "product_id": order.get("product_id"),
                "side": order.get("side"),
                "size": order.get("size"),
                "price": order.get("price"),
                "status": order.get("status"),
                "created_at": order.get("created_at")
            })
        
        logger.info(f"Retrieved {len(result['trades'])} trades")
    
    except Exception as e:
        result["error"] = f"Error getting trade history: {e}"
        logger.error(result["error"])
    
    return result

if __name__ == "__main__":
    # Example usage
    client = CoinbaseClient(demo_mode=True)
    
    # Execute trade strategy
    result = execute_trade_strategy("BTC-USD", TradingSignal.BUY, client, execute=False)
    print(f"Trade strategy result: {json.dumps(result, indent=2)}")
    
    # Get portfolio status
    portfolio = get_portfolio_status(client)
    print(f"Portfolio status: {json.dumps(portfolio, indent=2)}")
    
    # Get trade history
    history = get_trade_history(client)
    print(f"Trade history: {json.dumps(history, indent=2)}")
