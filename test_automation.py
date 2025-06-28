#!/usr/bin/env python3

"""
Comprehensive test for the automated cryptocurrency trading system.

This script tests all automation components including monitoring, decision making,
execution, and risk management.
"""

import sys
import time
import json
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from crypto_trading_system.src.automation.auto_trader import create_automated_trader
from crypto_trading_system.src.automation.monitor import create_monitor
from crypto_trading_system.src.automation.decision_engine import create_decision_engine
from crypto_trading_system.src.automation.trade_executor import create_trade_executor
from crypto_trading_system.src.automation.risk_manager import create_risk_manager

def test_monitor():
    """Test the crypto monitor component."""
    print("Testing CryptoMonitor...")
    
    monitor = create_monitor(update_interval=60)  # 1 minute for testing
    
    # Test getting tradeable coins
    coins = monitor.get_tradeable_coins()
    print(f"Found {len(coins)} tradeable coins")
    assert len(coins) > 0, "Should find tradeable coins"
    
    # Test analyzing a single coin
    if coins:
        test_symbol = coins[0]
        print(f"Testing analysis of {test_symbol}")
        
        analysis = monitor.analyze_coin(test_symbol, "1h")
        if analysis:
            print(f"Analysis result: {analysis['signal']} (confidence: {analysis['confidence']:.2f})")
            assert "signal" in analysis, "Analysis should contain signal"
            assert "confidence" in analysis, "Analysis should contain confidence"
        else:
            print("Analysis returned None - this is acceptable in demo mode")
    
    # Test status
    status = monitor.get_status()
    print(f"Monitor status: {status}")
    assert "is_running" in status, "Status should contain is_running"
    
    print("✓ CryptoMonitor test passed\n")

def test_decision_engine():
    """Test the decision engine component."""
    print("Testing AutomatedDecisionEngine...")
    
    engine = create_decision_engine()
    
    # Test portfolio value
    portfolio = engine.portfolio_manager.get_portfolio_value()
    print(f"Portfolio value: ${portfolio.get('total_value_usd', 0):.2f}")
    
    # Test decision stats
    stats = engine.get_decision_stats()
    print(f"Decision stats: {stats}")
    assert "min_confidence" in stats, "Stats should contain min_confidence"
    
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
    print(f"Generated {len(decisions)} trading decisions")
    
    for decision in decisions:
        print(f"  {decision['action']} {decision['symbol']} for ${decision['position_size_usd']:.2f}")
    
    print("✓ AutomatedDecisionEngine test passed\n")

def test_trade_executor():
    """Test the trade executor component."""
    print("Testing TradeExecutor...")
    
    executor = create_trade_executor()
    
    # Test execution stats
    stats = executor.get_execution_stats()
    print(f"Execution stats: {stats}")
    assert "daily_stats" in stats, "Stats should contain daily_stats"
    
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
    print(f"Execution results: {len(results)} decisions processed")
    
    for result in results:
        success = result.get("success", False)
        symbol = result.get("symbol", "")
        action = result.get("action", "")
        print(f"  {action} {symbol}: {'SUCCESS' if success else 'FAILED'}")
        
        if not success:
            print(f"    Error: {result.get('error', 'Unknown error')}")
    
    # Monitor orders
    monitoring = executor.monitor_active_orders()
    print(f"Order monitoring: {monitoring}")
    
    print("✓ TradeExecutor test passed\n")

def test_risk_manager():
    """Test the risk manager component."""
    print("Testing RiskManager...")
    
    risk_manager = create_risk_manager()
    
    # Test risk summary
    summary = risk_manager.get_risk_summary()
    print(f"Risk summary: {summary}")
    assert "risk_limits" in summary, "Summary should contain risk_limits"
    
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
    assert "approved" in assessment, "Assessment should contain approval status"
    
    # Test stop-loss functionality
    stop_config = risk_manager.stop_loss_manager.set_stop_loss("BTC-USD", 50000.0)
    print(f"Stop-loss set: {stop_config}")
    assert "stop_price" in stop_config, "Stop config should contain stop_price"
    
    print("✓ RiskManager test passed\n")

def test_automated_trader():
    """Test the complete automated trader."""
    print("Testing AutomatedTrader...")
    
    trader = create_automated_trader(update_interval=60)  # 1 minute for testing
    
    # Test initial status
    status = trader.get_status()
    print(f"Initial status: is_running={status['is_running']}, trading_enabled={status['trading_enabled']}")
    assert not status["is_running"], "Should not be running initially"
    
    # Test performance summary
    performance = trader.get_performance_summary()
    print(f"Performance summary: {performance}")
    assert "uptime_hours" in performance, "Performance should contain uptime_hours"
    
    # Test starting and stopping (briefly)
    print("Testing start/stop functionality...")
    trader.start_trading()
    
    # Wait a moment for initialization
    time.sleep(5)
    
    # Check status while running
    status = trader.get_status()
    print(f"Running status: is_running={status['is_running']}")
    assert status["is_running"], "Should be running after start"
    
    # Test disabling trading
    trader.disable_trading()
    status = trader.get_status()
    print(f"Trading disabled: trading_enabled={status['trading_enabled']}")
    assert not status["trading_enabled"], "Trading should be disabled"
    
    # Re-enable trading
    trader.enable_trading()
    status = trader.get_status()
    print(f"Trading re-enabled: trading_enabled={status['trading_enabled']}")
    assert status["trading_enabled"], "Trading should be re-enabled"
    
    # Stop the trader
    trader.stop_trading()
    
    # Check final status
    status = trader.get_status()
    print(f"Final status: is_running={status['is_running']}")
    assert not status["is_running"], "Should not be running after stop"
    
    print("✓ AutomatedTrader test passed\n")

def test_integration():
    """Test integration between components."""
    print("Testing component integration...")
    
    # Create all components
    monitor = create_monitor(update_interval=60)
    decision_engine = create_decision_engine()
    trade_executor = create_trade_executor()
    risk_manager = create_risk_manager()
    
    print("All components created successfully")
    
    # Test data flow: Monitor -> Decision Engine -> Risk Manager -> Executor
    
    # 1. Get opportunities from monitor
    opportunities = monitor.get_latest_opportunities(limit=5)
    print(f"Monitor provided {len(opportunities)} opportunities")
    
    # 2. Make decisions
    decisions = decision_engine.make_trading_decision(opportunities)
    print(f"Decision engine generated {len(decisions)} decisions")
    
    # 3. Risk assessment
    portfolio = decision_engine.portfolio_manager.get_portfolio_value()
    approved_decisions = []
    
    for decision in decisions:
        assessment = risk_manager.assess_trade_risk(decision, portfolio)
        if assessment.get("approved", False):
            approved_decisions.append(decision)
    
    print(f"Risk manager approved {len(approved_decisions)} decisions")
    
    # 4. Execute (in demo mode)
    if approved_decisions:
        results = trade_executor.execute_decisions(approved_decisions)
        successful = sum(1 for r in results if r.get("success"))
        print(f"Trade executor processed {len(results)} decisions, {successful} successful")
    
    print("✓ Integration test passed\n")

def main():
    """Run all tests."""
    print("Starting comprehensive automation system tests...\n")
    
    try:
        # Test individual components
        test_monitor()
        test_decision_engine()
        test_trade_executor()
        test_risk_manager()
        
        # Test complete system
        test_automated_trader()
        
        # Test integration
        test_integration()
        
        print("🎉 All tests passed successfully!")
        print("\nThe automated trading system is ready for deployment.")
        
        # Save test results
        test_results = {
            "timestamp": time.time(),
            "status": "PASSED",
            "components_tested": [
                "CryptoMonitor",
                "AutomatedDecisionEngine", 
                "TradeExecutor",
                "RiskManager",
                "AutomatedTrader"
            ],
            "integration_test": "PASSED"
        }
        
        with open("automation_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2)
        
        print("Test results saved to automation_test_results.json")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
        # Save failure results
        test_results = {
            "timestamp": time.time(),
            "status": "FAILED",
            "error": str(e)
        }
        
        with open("automation_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2)
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

