#!/usr/bin/env python3

"""
Run the automated cryptocurrency trading system.

This script starts the complete automated trading system with all features:
- Real-time monitoring of all tradeable coins
- Automated decision making based on analysis
- Live trade execution with Coinbase API
- Risk management and portfolio optimization
"""

import os
import sys
import time
import signal
import argparse
from pathlib import Path

# Add the project root directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from crypto_trading_system.src.automation.auto_trader import create_automated_trader

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\nShutdown signal received. Stopping automated trader...")
    if 'trader' in globals():
        trader.emergency_stop()
    sys.exit(0)

def main():
    """Main function to run the automated trader."""
    parser = argparse.ArgumentParser(description="Automated Cryptocurrency Trading System")
    parser.add_argument("--interval", type=int, default=3600, 
                       help="Analysis interval in seconds (default: 3600 = 1 hour)")
    parser.add_argument("--max-position", type=float, default=0.1,
                       help="Maximum position percentage (default: 0.1 = 10%)")
    parser.add_argument("--max-invested", type=float, default=0.8,
                       help="Maximum total invested percentage (default: 0.8 = 80%)")
    parser.add_argument("--min-confidence", type=float, default=0.75,
                       help="Minimum confidence for trades (default: 0.75)")
    parser.add_argument("--demo", action="store_true",
                       help="Run in demo mode (no real trades)")
    
    args = parser.parse_args()
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting Automated Cryptocurrency Trading System")
    print("=" * 60)
    print(f"Analysis Interval: {args.interval} seconds ({args.interval/3600:.1f} hours)")
    print(f"Max Position Size: {args.max_position*100:.1f}%")
    print(f"Max Total Invested: {args.max_invested*100:.1f}%")
    print(f"Min Confidence: {args.min_confidence*100:.1f}%")
    print(f"Demo Mode: {'Yes' if args.demo else 'No'}")
    print("=" * 60)
    
    # Create and configure the automated trader
    global trader
    trader = create_automated_trader(
        update_interval=args.interval,
        max_position_percentage=args.max_position,
        max_total_invested=args.max_invested
    )
    
    # Set minimum confidence
    trader.decision_engine.min_confidence = args.min_confidence
    
    try:
        # Start the automated trading system
        trader.start_trading()
        
        print("✅ Automated trading system started successfully!")
        print("\nSystem Status:")
        print("- Monitoring: Active")
        print("- Decision Engine: Active") 
        print("- Trade Execution: Active")
        print("- Risk Management: Active")
        print("\nPress Ctrl+C to stop the system safely")
        print("-" * 60)
        
        # Main monitoring loop
        while True:
            time.sleep(30)  # Check status every 30 seconds
            
            # Get and display status
            status = trader.get_status()
            performance = trader.get_performance_summary()
            
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] System Status:")
            print(f"  Running: {status['is_running']}")
            print(f"  Trading Enabled: {status['trading_enabled']}")
            print(f"  Uptime: {performance['uptime_hours']:.1f} hours")
            print(f"  Total Trades: {performance['total_trades']}")
            print(f"  Success Rate: {performance['success_rate']:.1f}%")
            print(f"  Total Volume: ${performance['total_volume']:.2f}")
            
            # Show risk alerts if any
            risk_summary = status.get('risk_summary', {})
            recent_alerts = risk_summary.get('recent_alerts', [])
            if recent_alerts:
                print(f"  ⚠️  Risk Alerts: {len(recent_alerts)}")
                for alert in recent_alerts[-3:]:  # Show last 3 alerts
                    print(f"    - {alert.get('message', 'Unknown alert')}")
            
            print("-" * 60)
    
    except KeyboardInterrupt:
        print("\nShutdown requested by user...")
    except Exception as e:
        print(f"\n❌ Error in automated trader: {e}")
    finally:
        # Ensure clean shutdown
        if trader.is_running:
            print("Stopping automated trading system...")
            trader.stop_trading()
            print("✅ System stopped safely")

if __name__ == "__main__":
    main()

