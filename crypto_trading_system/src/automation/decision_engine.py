"""
Automated decision engine for cryptocurrency trading.

This module makes automated trading decisions based on analysis results,
portfolio allocation, and risk management parameters.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json

from ..api.clients import CoinbaseClient
from ..models.data_models import TradingSignal
from ..utils.helpers import setup_logging
from ..config.settings import DEMO_MODE

# Set up logging
logger = setup_logging("decision_engine")

class PortfolioManager:
    """
    Manages portfolio allocation and position sizing.
    """
    
    def __init__(self, max_position_percentage: float = 0.1, 
                 max_total_invested: float = 0.8,
                 min_trade_amount: float = 10.0):
        """
        Initialize portfolio manager.
        
        Args:
            max_position_percentage: Maximum percentage per position (0.1 = 10%)
            max_total_invested: Maximum total portfolio percentage invested
            min_trade_amount: Minimum trade amount in USD
        """
        self.max_position_percentage = max_position_percentage
        self.max_total_invested = max_total_invested
        self.min_trade_amount = min_trade_amount
        self.coinbase_client = CoinbaseClient()
        
        logger.info(f"Portfolio manager initialized: max_position={max_position_percentage*100}%, "
                   f"max_invested={max_total_invested*100}%, min_trade=${min_trade_amount}")
    
    def get_portfolio_value(self) -> Dict[str, Any]:
        """
        Get current portfolio value and allocation.
        
        Returns:
            Portfolio information including total value and positions
        """
        try:
            accounts = self.coinbase_client.get_accounts()
            
            if "error" in accounts:
                logger.error(f"Error fetching accounts: {accounts['error']}")
                return {"error": accounts["error"]}
            
            total_value_usd = 0.0
            positions = {}
            cash_balance = 0.0
            
            if "accounts" in accounts:
                for account in accounts["accounts"]:
                    currency = account.get("currency", "")
                    balance = float(account.get("balance", 0))
                    
                    if balance > 0:
                        if currency == "USD":
                            cash_balance = balance
                            total_value_usd += balance
                        else:
                            # Get current price for crypto positions
                            symbol = f"{currency}-USD"
                            ticker = self.coinbase_client.get_product_ticker(symbol)
                            
                            if ticker and "price" in ticker:
                                price = float(ticker["price"])
                                value_usd = balance * price
                                total_value_usd += value_usd
                                
                                positions[currency] = {
                                    "balance": balance,
                                    "price": price,
                                    "value_usd": value_usd,
                                    "percentage": 0  # Will be calculated below
                                }
            
            # Calculate percentages
            if total_value_usd > 0:
                for currency in positions:
                    positions[currency]["percentage"] = positions[currency]["value_usd"] / total_value_usd
            
            portfolio_info = {
                "total_value_usd": total_value_usd,
                "cash_balance": cash_balance,
                "cash_percentage": cash_balance / total_value_usd if total_value_usd > 0 else 0,
                "positions": positions,
                "invested_percentage": (total_value_usd - cash_balance) / total_value_usd if total_value_usd > 0 else 0
            }
            
            logger.debug(f"Portfolio value: ${total_value_usd:.2f}, Cash: ${cash_balance:.2f}")
            return portfolio_info
            
        except Exception as e:
            logger.error(f"Error getting portfolio value: {e}")
            return {"error": str(e)}
    
    def calculate_position_size(self, symbol: str, portfolio_value: float, 
                              signal_strength: float) -> float:
        """
        Calculate optimal position size for a trade.
        
        Args:
            symbol: Trading symbol (e.g., "BTC-USD")
            portfolio_value: Total portfolio value
            signal_strength: Signal strength (0.0 to 1.0)
            
        Returns:
            Position size in USD
        """
        # Base position size from max percentage
        base_size = portfolio_value * self.max_position_percentage
        
        # Adjust based on signal strength
        adjusted_size = base_size * signal_strength
        
        # Ensure minimum trade amount
        if adjusted_size < self.min_trade_amount:
            if base_size >= self.min_trade_amount:
                adjusted_size = self.min_trade_amount
            else:
                adjusted_size = 0  # Portfolio too small for this position
        
        logger.debug(f"Position size for {symbol}: ${adjusted_size:.2f} "
                    f"(base: ${base_size:.2f}, strength: {signal_strength:.2f})")
        
        return adjusted_size
    
    def can_open_position(self, symbol: str, position_size: float) -> Tuple[bool, str]:
        """
        Check if a new position can be opened.
        
        Args:
            symbol: Trading symbol
            position_size: Desired position size in USD
            
        Returns:
            Tuple of (can_open, reason)
        """
        portfolio = self.get_portfolio_value()
        
        if "error" in portfolio:
            return False, f"Portfolio error: {portfolio['error']}"
        
        total_value = portfolio["total_value_usd"]
        cash_balance = portfolio["cash_balance"]
        invested_percentage = portfolio["invested_percentage"]
        
        # Check if we have enough cash
        if position_size > cash_balance:
            return False, f"Insufficient cash: ${cash_balance:.2f} < ${position_size:.2f}"
        
        # Check if we're not over-invested
        new_invested_percentage = (invested_percentage * total_value + position_size) / total_value
        if new_invested_percentage > self.max_total_invested:
            return False, f"Would exceed max invested percentage: {new_invested_percentage:.1%} > {self.max_total_invested:.1%}"
        
        # Check if we already have a position in this asset
        currency = symbol.split("-")[0]
        if currency in portfolio["positions"]:
            current_percentage = portfolio["positions"][currency]["percentage"]
            new_percentage = (portfolio["positions"][currency]["value_usd"] + position_size) / total_value
            
            if new_percentage > self.max_position_percentage:
                return False, f"Would exceed max position percentage for {currency}: {new_percentage:.1%} > {self.max_position_percentage:.1%}"
        
        return True, "Position can be opened"


class AutomatedDecisionEngine:
    """
    Automated decision engine for cryptocurrency trading.
    
    Makes trading decisions based on analysis results and portfolio management rules.
    """
    
    def __init__(self, max_position_percentage: float = 0.1,
                 max_total_invested: float = 0.8,
                 min_confidence: float = 0.75,
                 min_trade_amount: float = 10.0):
        """
        Initialize the decision engine.
        
        Args:
            max_position_percentage: Maximum percentage per position
            max_total_invested: Maximum total portfolio percentage invested
            min_confidence: Minimum confidence for trade execution
            min_trade_amount: Minimum trade amount in USD
        """
        self.portfolio_manager = PortfolioManager(
            max_position_percentage=max_position_percentage,
            max_total_invested=max_total_invested,
            min_trade_amount=min_trade_amount
        )
        self.min_confidence = min_confidence
        self.coinbase_client = CoinbaseClient()
        
        # Track recent decisions to avoid over-trading
        self.recent_decisions = []
        self.decision_cooldown = 300  # 5 minutes between decisions for same symbol
        
        logger.info(f"Decision engine initialized with min_confidence={min_confidence}")
    
    def should_buy(self, analysis_result: Dict[str, Any]) -> Tuple[bool, str, float]:
        """
        Determine if we should buy based on analysis result.
        
        Args:
            analysis_result: Analysis result from monitoring system
            
        Returns:
            Tuple of (should_buy, reason, confidence)
        """
        signal = analysis_result.get("signal", "NEUTRAL")
        confidence = analysis_result.get("confidence", 0.0)
        symbol = analysis_result.get("symbol", "")
        
        # Check signal type
        if signal not in ["BUY", "STRONG_BUY"]:
            return False, f"Signal is {signal}, not a buy signal", confidence
        
        # Check confidence level
        if confidence < self.min_confidence:
            return False, f"Confidence {confidence:.2f} below minimum {self.min_confidence}", confidence
        
        # Check cooldown period
        if self._is_in_cooldown(symbol):
            return False, f"Symbol {symbol} is in cooldown period", confidence
        
        # Additional checks can be added here (e.g., market conditions, volatility)
        
        return True, f"Strong {signal} signal with {confidence:.2f} confidence", confidence
    
    def should_sell(self, symbol: str, current_position: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Determine if we should sell a current position.
        
        Args:
            symbol: Trading symbol
            current_position: Current position information
            
        Returns:
            Tuple of (should_sell, reason)
        """
        # This would typically involve:
        # 1. Stop-loss checks
        # 2. Take-profit checks
        # 3. Signal reversal checks
        # 4. Time-based exits
        
        # For now, implement basic logic
        # In a real system, this would be much more sophisticated
        
        return False, "No sell conditions met"
    
    def make_trading_decision(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Make trading decisions based on available opportunities.
        
        Args:
            opportunities: List of trading opportunities from monitor
            
        Returns:
            List of trading decisions to execute
        """
        decisions = []
        portfolio = self.portfolio_manager.get_portfolio_value()
        
        if "error" in portfolio:
            logger.error(f"Cannot make decisions due to portfolio error: {portfolio['error']}")
            return decisions
        
        total_value = portfolio["total_value_usd"]
        
        logger.info(f"Making trading decisions for {len(opportunities)} opportunities")
        logger.info(f"Portfolio value: ${total_value:.2f}")
        
        # Sort opportunities by potential return
        sorted_opportunities = sorted(opportunities, 
                                    key=lambda x: x.get("potential_return", 0), 
                                    reverse=True)
        
        for opportunity in sorted_opportunities:
            symbol = opportunity.get("symbol", "")
            
            # Check if we should buy
            should_buy, reason, confidence = self.should_buy(opportunity)
            
            if should_buy:
                # Calculate position size
                position_size = self.portfolio_manager.calculate_position_size(
                    symbol, total_value, confidence
                )
                
                # Check if we can open the position
                can_open, open_reason = self.portfolio_manager.can_open_position(
                    symbol, position_size
                )
                
                if can_open and position_size > 0:
                    decision = {
                        "action": "BUY",
                        "symbol": symbol,
                        "position_size_usd": position_size,
                        "confidence": confidence,
                        "reason": reason,
                        "timestamp": datetime.now().isoformat(),
                        "timeframe": opportunity.get("timeframe", "1h"),
                        "analysis_data": opportunity
                    }
                    decisions.append(decision)
                    
                    # Add to recent decisions for cooldown tracking
                    self._add_recent_decision(symbol)
                    
                    logger.info(f"Decision: BUY {symbol} for ${position_size:.2f} "
                              f"(confidence: {confidence:.2f})")
                else:
                    logger.debug(f"Cannot open position for {symbol}: {open_reason}")
            else:
                logger.debug(f"Not buying {symbol}: {reason}")
        
        # Check existing positions for sell decisions
        for currency, position in portfolio.get("positions", {}).items():
            symbol = f"{currency}-USD"
            should_sell, sell_reason = self.should_sell(symbol, position)
            
            if should_sell:
                decision = {
                    "action": "SELL",
                    "symbol": symbol,
                    "position_size_usd": position["value_usd"],
                    "balance": position["balance"],
                    "reason": sell_reason,
                    "timestamp": datetime.now().isoformat()
                }
                decisions.append(decision)
                
                logger.info(f"Decision: SELL {symbol} for ${position['value_usd']:.2f}")
        
        logger.info(f"Generated {len(decisions)} trading decisions")
        return decisions
    
    def _is_in_cooldown(self, symbol: str) -> bool:
        """Check if symbol is in cooldown period."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.decision_cooldown)
        
        for decision in self.recent_decisions:
            if (decision["symbol"] == symbol and 
                datetime.fromisoformat(decision["timestamp"]) > cutoff):
                return True
        
        return False
    
    def _add_recent_decision(self, symbol: str):
        """Add a decision to recent decisions tracking."""
        self.recent_decisions.append({
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        })
        
        # Clean old decisions
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.decision_cooldown * 2)
        self.recent_decisions = [
            d for d in self.recent_decisions
            if datetime.fromisoformat(d["timestamp"]) > cutoff
        ]
    
    def get_decision_stats(self) -> Dict[str, Any]:
        """
        Get statistics about recent decisions.
        
        Returns:
            Decision statistics
        """
        now = datetime.now()
        last_hour = now - timedelta(hours=1)
        last_day = now - timedelta(days=1)
        
        recent_hour = [
            d for d in self.recent_decisions
            if datetime.fromisoformat(d["timestamp"]) > last_hour
        ]
        
        recent_day = [
            d for d in self.recent_decisions
            if datetime.fromisoformat(d["timestamp"]) > last_day
        ]
        
        return {
            "decisions_last_hour": len(recent_hour),
            "decisions_last_day": len(recent_day),
            "total_tracked_decisions": len(self.recent_decisions),
            "min_confidence": self.min_confidence,
            "max_position_percentage": self.portfolio_manager.max_position_percentage,
            "max_total_invested": self.portfolio_manager.max_total_invested
        }


def create_decision_engine(max_position_percentage: float = 0.1,
                          max_total_invested: float = 0.8,
                          min_confidence: float = 0.75) -> AutomatedDecisionEngine:
    """
    Create and configure a decision engine instance.
    
    Args:
        max_position_percentage: Maximum percentage per position
        max_total_invested: Maximum total portfolio percentage invested
        min_confidence: Minimum confidence for trade execution
        
    Returns:
        Configured AutomatedDecisionEngine instance
    """
    return AutomatedDecisionEngine(
        max_position_percentage=max_position_percentage,
        max_total_invested=max_total_invested,
        min_confidence=min_confidence
    )


if __name__ == "__main__":
    # Test the decision engine
    engine = create_decision_engine()
    
    # Test portfolio value
    portfolio = engine.portfolio_manager.get_portfolio_value()
    print(f"Portfolio: {portfolio}")
    
    # Test decision stats
    stats = engine.get_decision_stats()
    print(f"Decision stats: {stats}")
    
    # Test with sample opportunities
    sample_opportunities = [
        {
            "symbol": "BTC-USD",
            "signal": "BUY",
            "confidence": 0.85,
            "potential_return": 1.7,
            "timeframe": "1h"
        },
        {
            "symbol": "ETH-USD", 
            "signal": "STRONG_BUY",
            "confidence": 0.92,
            "potential_return": 1.84,
            "timeframe": "1h"
        }
    ]
    
    decisions = engine.make_trading_decision(sample_opportunities)
    print(f"Trading decisions: {decisions}")

