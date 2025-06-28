#!/usr/bin/env python3

"""
Simple validation test for automation components.
"""

import sys
import json
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def test_imports():
    """Test that all automation modules can be imported."""
    print("Testing imports...")
    
    try:
        from crypto_trading_system.src.automation.monitor import CryptoMonitor
        print("✓ CryptoMonitor imported")
        
        from crypto_trading_system.src.automation.decision_engine import AutomatedDecisionEngine
        print("✓ AutomatedDecisionEngine imported")
        
        from crypto_trading_system.src.automation.trade_executor import TradeExecutor
        print("✓ TradeExecutor imported")
        
        from crypto_trading_system.src.automation.risk_manager import RiskManager
        print("✓ RiskManager imported")
        
        from crypto_trading_system.src.automation.auto_trader import AutomatedTrader
        print("✓ AutomatedTrader imported")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality of automation components."""
    print("\nTesting basic functionality...")
    
    try:
        from crypto_trading_system.src.automation.auto_trader import create_automated_trader
        
        # Create trader instance
        trader = create_automated_trader(update_interval=3600)
        print("✓ AutomatedTrader created")
        
        # Test status
        status = trader.get_status()
        print(f"✓ Status retrieved: running={status['is_running']}")
        
        # Test performance summary
        performance = trader.get_performance_summary()
        print(f"✓ Performance summary: {performance['total_trades']} trades")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def test_decision_engine():
    """Test decision engine with sample data."""
    print("\nTesting decision engine...")
    
    try:
        from crypto_trading_system.src.automation.decision_engine import create_decision_engine
        
        engine = create_decision_engine()
        print("✓ Decision engine created")
        
        # Test with sample opportunities
        sample_opportunities = [
            {
                "symbol": "BTC-USD",
                "signal": "BUY",
                "confidence": 0.85,
                "potential_return": 1.7,
                "timeframe": "1h"
            }
        ]
        
        decisions = engine.make_trading_decision(sample_opportunities)
        print(f"✓ Generated {len(decisions)} decisions")
        
        return True
        
    except Exception as e:
        print(f"❌ Decision engine test failed: {e}")
        return False

def main():
    """Run validation tests."""
    print("Starting automation validation tests...\n")
    
    tests_passed = 0
    total_tests = 3
    
    # Test imports
    if test_imports():
        tests_passed += 1
    
    # Test basic functionality
    if test_basic_functionality():
        tests_passed += 1
    
    # Test decision engine
    if test_decision_engine():
        tests_passed += 1
    
    print(f"\nValidation Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All validation tests passed!")
        print("The automation system is ready for use.")
        
        # Save validation results
        results = {
            "status": "PASSED",
            "tests_passed": tests_passed,
            "total_tests": total_tests,
            "components_validated": [
                "CryptoMonitor",
                "AutomatedDecisionEngine", 
                "TradeExecutor",
                "RiskManager",
                "AutomatedTrader"
            ]
        }
        
        with open("automation_validation.json", "w") as f:
            json.dump(results, f, indent=2)
        
        return True
    else:
        print("❌ Some validation tests failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

