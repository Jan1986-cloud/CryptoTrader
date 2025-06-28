"""
Risk management and portfolio optimization for automated cryptocurrency trading.

This module implements comprehensive risk management including stop-losses,
position sizing, portfolio rebalancing, and risk metrics monitoring.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
import math

from ..api.clients import CoinbaseClient
from ..models.data_models import TradingSignal
from ..utils.helpers import setup_logging
from ..config.settings import DEMO_MODE

# Set up logging
logger = setup_logging("risk_manager")

class RiskMetrics:
    """
    Calculates and tracks risk metrics for the portfolio.
    """
    
    def __init__(self):
        """Initialize risk metrics calculator."""
        self.price_history = {}
        self.portfolio_history = []
        
    def calculate_volatility(self, prices: List[float], period: int = 20) -> float:
        """
        Calculate price volatility (standard deviation of returns).
        
        Args:
            prices: List of historical prices
            period: Period for calculation
            
        Returns:
            Volatility as a decimal (0.1 = 10%)
        """
        if len(prices) < period + 1:
            return 0.0
        
        # Calculate returns
        returns = []
        for i in range(1, min(len(prices), period + 1)):
            if prices[i-1] > 0:
                returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        if len(returns) < 2:
            return 0.0
        
        # Calculate standard deviation
        mean_return = sum(returns) / len(returns)
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        volatility = math.sqrt(variance)
        
        return volatility
    
    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio for performance evaluation.
        
        Args:
            returns: List of portfolio returns
            risk_free_rate: Annual risk-free rate
            
        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0
        
        mean_return = sum(returns) / len(returns)
        
        # Annualize returns (assuming daily returns)
        annual_return = mean_return * 365
        
        # Calculate standard deviation
        variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
        volatility = math.sqrt(variance) * math.sqrt(365)  # Annualize volatility
        
        if volatility == 0:
            return 0.0
        
        sharpe_ratio = (annual_return - risk_free_rate) / volatility
        return sharpe_ratio
    
    def calculate_max_drawdown(self, portfolio_values: List[float]) -> float:
        """
        Calculate maximum drawdown from peak.
        
        Args:
            portfolio_values: List of portfolio values over time
            
        Returns:
            Maximum drawdown as a decimal (0.1 = 10% drawdown)
        """
        if len(portfolio_values) < 2:
            return 0.0
        
        peak = portfolio_values[0]
        max_drawdown = 0.0
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            
            drawdown = (peak - value) / peak if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown


class StopLossManager:
    """
    Manages stop-loss orders and position protection.
    """
    
    def __init__(self, default_stop_loss: float = 0.1, trailing_stop: bool = True):
        """
        Initialize stop-loss manager.
        
        Args:
            default_stop_loss: Default stop-loss percentage (0.1 = 10%)
            trailing_stop: Whether to use trailing stops
        """
        self.default_stop_loss = default_stop_loss
        self.trailing_stop = trailing_stop
        self.position_stops = {}
        self.coinbase_client = CoinbaseClient()
        
        logger.info(f"Stop-loss manager initialized: {default_stop_loss*100}% default stop")
    
    def set_stop_loss(self, symbol: str, entry_price: float, 
                     stop_percentage: Optional[float] = None) -> Dict[str, Any]:
        """
        Set stop-loss for a position.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price for the position
            stop_percentage: Custom stop-loss percentage
            
        Returns:
            Stop-loss configuration
        """
        stop_pct = stop_percentage or self.default_stop_loss
        stop_price = entry_price * (1 - stop_pct)
        
        stop_config = {
            "symbol": symbol,
            "entry_price": entry_price,
            "stop_percentage": stop_pct,
            "stop_price": stop_price,
            "highest_price": entry_price,  # For trailing stops
            "created_at": datetime.now().isoformat(),
            "triggered": False
        }
        
        self.position_stops[symbol] = stop_config
        
        logger.info(f"Stop-loss set for {symbol}: {stop_pct*100}% at ${stop_price:.2f}")
        return stop_config
    
    def update_trailing_stop(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """
        Update trailing stop-loss based on current price.
        
        Args:
            symbol: Trading symbol
            current_price: Current market price
            
        Returns:
            Updated stop configuration
        """
        if symbol not in self.position_stops:
            return {"error": f"No stop-loss found for {symbol}"}
        
        stop_config = self.position_stops[symbol]
        
        if not self.trailing_stop:
            return stop_config
        
        # Update highest price if current price is higher
        if current_price > stop_config["highest_price"]:
            stop_config["highest_price"] = current_price
            
            # Update trailing stop price
            new_stop_price = current_price * (1 - stop_config["stop_percentage"])
            
            # Only move stop up, never down
            if new_stop_price > stop_config["stop_price"]:
                old_stop = stop_config["stop_price"]
                stop_config["stop_price"] = new_stop_price
                stop_config["updated_at"] = datetime.now().isoformat()
                
                logger.debug(f"Trailing stop updated for {symbol}: "
                           f"${old_stop:.2f} -> ${new_stop_price:.2f}")
        
        return stop_config
    
    def check_stop_triggers(self, current_prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Check if any stop-losses should be triggered.
        
        Args:
            current_prices: Dictionary of current prices by symbol
            
        Returns:
            List of triggered stops
        """
        triggered_stops = []
        
        for symbol, stop_config in self.position_stops.items():
            if stop_config["triggered"]:
                continue
            
            current_price = current_prices.get(symbol)
            if current_price is None:
                continue
            
            # Update trailing stop
            self.update_trailing_stop(symbol, current_price)
            
            # Check if stop should trigger
            if current_price <= stop_config["stop_price"]:
                stop_config["triggered"] = True
                stop_config["trigger_price"] = current_price
                stop_config["triggered_at"] = datetime.now().isoformat()
                
                triggered_stops.append({
                    "symbol": symbol,
                    "trigger_price": current_price,
                    "stop_price": stop_config["stop_price"],
                    "entry_price": stop_config["entry_price"],
                    "loss_percentage": (stop_config["entry_price"] - current_price) / stop_config["entry_price"],
                    "config": stop_config
                })
                
                logger.warning(f"Stop-loss triggered for {symbol}: "
                             f"${current_price:.2f} <= ${stop_config['stop_price']:.2f}")
        
        return triggered_stops
    
    def remove_stop_loss(self, symbol: str) -> bool:
        """
        Remove stop-loss for a symbol (when position is closed).
        
        Args:
            symbol: Trading symbol
            
        Returns:
            True if removed successfully
        """
        if symbol in self.position_stops:
            del self.position_stops[symbol]
            logger.info(f"Stop-loss removed for {symbol}")
            return True
        return False


class PortfolioOptimizer:
    """
    Optimizes portfolio allocation and rebalancing.
    """
    
    def __init__(self, target_allocations: Optional[Dict[str, float]] = None,
                 rebalance_threshold: float = 0.05):
        """
        Initialize portfolio optimizer.
        
        Args:
            target_allocations: Target allocation percentages by asset
            rebalance_threshold: Threshold for triggering rebalancing (5%)
        """
        self.target_allocations = target_allocations or {}
        self.rebalance_threshold = rebalance_threshold
        self.coinbase_client = CoinbaseClient()
        
        logger.info(f"Portfolio optimizer initialized with {rebalance_threshold*100}% rebalance threshold")
    
    def calculate_current_allocation(self, portfolio: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate current portfolio allocation percentages.
        
        Args:
            portfolio: Portfolio information from portfolio manager
            
        Returns:
            Current allocation percentages by asset
        """
        allocations = {}
        total_value = portfolio.get("total_value_usd", 0)
        
        if total_value <= 0:
            return allocations
        
        # Cash allocation
        cash_balance = portfolio.get("cash_balance", 0)
        allocations["USD"] = cash_balance / total_value
        
        # Crypto allocations
        positions = portfolio.get("positions", {})
        for currency, position in positions.items():
            allocations[currency] = position.get("percentage", 0)
        
        return allocations
    
    def identify_rebalancing_needs(self, current_allocations: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Identify assets that need rebalancing.
        
        Args:
            current_allocations: Current allocation percentages
            
        Returns:
            List of rebalancing actions needed
        """
        rebalancing_actions = []
        
        for asset, target_pct in self.target_allocations.items():
            current_pct = current_allocations.get(asset, 0)
            difference = abs(current_pct - target_pct)
            
            if difference > self.rebalance_threshold:
                action = "buy" if current_pct < target_pct else "sell"
                
                rebalancing_actions.append({
                    "asset": asset,
                    "action": action,
                    "current_percentage": current_pct,
                    "target_percentage": target_pct,
                    "difference": difference,
                    "priority": difference  # Higher difference = higher priority
                })
        
        # Sort by priority (highest difference first)
        rebalancing_actions.sort(key=lambda x: x["priority"], reverse=True)
        
        return rebalancing_actions
    
    def calculate_optimal_position_sizes(self, opportunities: List[Dict[str, Any]], 
                                       available_capital: float) -> Dict[str, float]:
        """
        Calculate optimal position sizes for multiple opportunities.
        
        Args:
            opportunities: List of trading opportunities
            available_capital: Available capital for allocation
            
        Returns:
            Optimal position sizes by symbol
        """
        if not opportunities or available_capital <= 0:
            return {}
        
        # Simple equal-weight allocation with confidence weighting
        total_confidence = sum(opp.get("confidence", 0) for opp in opportunities)
        
        if total_confidence <= 0:
            return {}
        
        position_sizes = {}
        
        for opportunity in opportunities:
            symbol = opportunity.get("symbol", "")
            confidence = opportunity.get("confidence", 0)
            
            # Weight allocation by confidence
            weight = confidence / total_confidence
            position_size = available_capital * weight
            
            position_sizes[symbol] = position_size
        
        return position_sizes


class RiskManager:
    """
    Comprehensive risk management system.
    """
    
    def __init__(self, max_portfolio_risk: float = 0.02,
                 max_position_risk: float = 0.1,
                 max_daily_loss: float = 0.05):
        """
        Initialize risk manager.
        
        Args:
            max_portfolio_risk: Maximum portfolio risk per day (2%)
            max_position_risk: Maximum risk per position (10%)
            max_daily_loss: Maximum daily loss threshold (5%)
        """
        self.max_portfolio_risk = max_portfolio_risk
        self.max_position_risk = max_position_risk
        self.max_daily_loss = max_daily_loss
        
        self.risk_metrics = RiskMetrics()
        self.stop_loss_manager = StopLossManager()
        self.portfolio_optimizer = PortfolioOptimizer()
        self.coinbase_client = CoinbaseClient()
        
        # Risk tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.risk_alerts = []
        self.last_reset = datetime.now().date()
        
        logger.info(f"Risk manager initialized: max portfolio risk {max_portfolio_risk*100}%")
    
    def assess_trade_risk(self, decision: Dict[str, Any], 
                         portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk for a proposed trade.
        
        Args:
            decision: Trading decision to assess
            portfolio: Current portfolio state
            
        Returns:
            Risk assessment result
        """
        symbol = decision.get("symbol", "")
        position_size = decision.get("position_size_usd", 0)
        confidence = decision.get("confidence", 0)
        
        total_value = portfolio.get("total_value_usd", 0)
        
        risk_assessment = {
            "symbol": symbol,
            "approved": True,
            "risk_score": 0.0,
            "warnings": [],
            "adjustments": {}
        }
        
        # Check position size risk
        if total_value > 0:
            position_risk = position_size / total_value
            if position_risk > self.max_position_risk:
                risk_assessment["warnings"].append(
                    f"Position size {position_risk:.1%} exceeds max {self.max_position_risk:.1%}"
                )
                # Suggest adjustment
                max_position_size = total_value * self.max_position_risk
                risk_assessment["adjustments"]["position_size_usd"] = max_position_size
        
        # Check daily loss limits
        if self.daily_pnl < -self.max_daily_loss * total_value:
            risk_assessment["approved"] = False
            risk_assessment["warnings"].append(
                f"Daily loss limit exceeded: ${abs(self.daily_pnl):.2f}"
            )
        
        # Check confidence level
        if confidence < 0.7:
            risk_assessment["warnings"].append(
                f"Low confidence signal: {confidence:.2f}"
            )
            risk_assessment["risk_score"] += 0.3
        
        # Calculate overall risk score
        risk_assessment["risk_score"] = min(1.0, risk_assessment["risk_score"])
        
        return risk_assessment
    
    def monitor_portfolio_risk(self, portfolio: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor overall portfolio risk metrics.
        
        Args:
            portfolio: Current portfolio state
            
        Returns:
            Risk monitoring results
        """
        total_value = portfolio.get("total_value_usd", 0)
        positions = portfolio.get("positions", {})
        
        # Calculate concentration risk
        max_position_pct = 0
        if positions:
            max_position_pct = max(pos.get("percentage", 0) for pos in positions.values())
        
        # Check for risk alerts
        alerts = []
        
        if max_position_pct > self.max_position_risk:
            alerts.append({
                "type": "concentration_risk",
                "message": f"Position concentration {max_position_pct:.1%} exceeds limit",
                "severity": "high"
            })
        
        if self.daily_pnl < -self.max_daily_loss * total_value:
            alerts.append({
                "type": "daily_loss_limit",
                "message": f"Daily loss ${abs(self.daily_pnl):.2f} exceeds limit",
                "severity": "critical"
            })
        
        # Store alerts
        self.risk_alerts.extend(alerts)
        
        return {
            "total_portfolio_value": total_value,
            "max_position_concentration": max_position_pct,
            "daily_pnl": self.daily_pnl,
            "daily_trades": self.daily_trades,
            "risk_alerts": alerts,
            "risk_limits": {
                "max_portfolio_risk": self.max_portfolio_risk,
                "max_position_risk": self.max_position_risk,
                "max_daily_loss": self.max_daily_loss
            }
        }
    
    def update_daily_pnl(self, pnl_change: float):
        """
        Update daily P&L tracking.
        
        Args:
            pnl_change: Change in P&L (positive for profit, negative for loss)
        """
        today = datetime.now().date()
        
        # Reset daily tracking if new day
        if today != self.last_reset:
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.last_reset = today
            logger.info("Daily risk tracking reset for new day")
        
        self.daily_pnl += pnl_change
        self.daily_trades += 1
        
        logger.debug(f"Daily P&L updated: ${self.daily_pnl:.2f} ({self.daily_trades} trades)")
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive risk summary.
        
        Returns:
            Risk summary information
        """
        return {
            "daily_pnl": self.daily_pnl,
            "daily_trades": self.daily_trades,
            "active_stops": len(self.stop_loss_manager.position_stops),
            "risk_alerts_count": len(self.risk_alerts),
            "recent_alerts": self.risk_alerts[-5:] if self.risk_alerts else [],
            "risk_limits": {
                "max_portfolio_risk": self.max_portfolio_risk,
                "max_position_risk": self.max_position_risk,
                "max_daily_loss": self.max_daily_loss
            }
        }


def create_risk_manager(max_portfolio_risk: float = 0.02,
                       max_position_risk: float = 0.1) -> RiskManager:
    """
    Create and configure a risk manager instance.
    
    Args:
        max_portfolio_risk: Maximum portfolio risk per day
        max_position_risk: Maximum risk per position
        
    Returns:
        Configured RiskManager instance
    """
    return RiskManager(
        max_portfolio_risk=max_portfolio_risk,
        max_position_risk=max_position_risk
    )


if __name__ == "__main__":
    # Test the risk manager
    risk_manager = create_risk_manager()
    
    # Test risk summary
    summary = risk_manager.get_risk_summary()
    print(f"Risk summary: {summary}")
    
    # Test trade risk assessment
    sample_decision = {
        "symbol": "BTC-USD",
        "position_size_usd": 1000.0,
        "confidence": 0.85
    }
    
    sample_portfolio = {
        "total_value_usd": 10000.0,
        "positions": {}
    }
    
    assessment = risk_manager.assess_trade_risk(sample_decision, sample_portfolio)
    print(f"Risk assessment: {assessment}")

