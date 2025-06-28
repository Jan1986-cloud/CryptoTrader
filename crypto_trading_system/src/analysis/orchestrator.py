"""
Scoring and analysis orchestrator for the Cryptocurrency Trading System.

This module coordinates the analysis of cryptocurrencies across different
analysis modules and combines the results into a final recommendation.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from ..utils.helpers import setup_logging
from .technical import analyze_technical
from .sentiment import analyze_sentiment
from .market import analyze_market
from .project import analyze_project

# Set up logging
logger = setup_logging("analysis_orchestrator")

def analyze_cryptocurrency(symbol: str, interval: str = "1d", days: int = 30) -> Dict[str, Any]:
    """
    Perform comprehensive analysis of a cryptocurrency.
    
    Args:
        symbol: The trading pair symbol (e.g., 'BTC-USD')
        interval: The time interval ('1h', '1d', '7d', '30d', '90d')
        days: Number of days of historical data to analyze
        
    Returns:
        Dictionary with analysis results and trading recommendation
    """
    logger.info(f"Starting comprehensive analysis for {symbol} with interval {interval}")
    
    results = {
        "symbol": symbol,
        "timestamp": datetime.now().isoformat(),
        "interval": interval,
        "days_analyzed": days,
        "scores": {},
        "recommendation": {}
    }
    
    # Technical analysis
    technical_scores = analyze_technical(symbol, interval, days)
    if technical_scores:
        results["scores"]["technical"] = technical_scores
    
    # Sentiment analysis
    sentiment_scores = analyze_sentiment(symbol)
    if sentiment_scores:
        results["scores"]["sentiment"] = sentiment_scores
    
    # Market data analysis
    market_scores = analyze_market(symbol)
    if market_scores:
        results["scores"]["market"] = market_scores
    
    # Project fundamentals analysis
    project_scores = analyze_project(symbol)
    if project_scores:
        results["scores"]["project"] = project_scores
    
    # Generate trading recommendation
    results["recommendation"] = generate_recommendation(results["scores"], interval)
    
    logger.info(f"Completed comprehensive analysis for {symbol}")
    return results

def generate_recommendation(scores: Dict[str, Dict[str, float]], interval: str) -> Dict[str, Any]:
    """
    Generate trading recommendation based on analysis scores.
    
    Args:
        scores: Dictionary with scores from different analysis modules
        interval: The time interval used for analysis
        
    Returns:
        Dictionary with trading recommendation
    """
    recommendation = {
        "action": "HOLD",  # Default recommendation
        "confidence": 0.0,
        "reasoning": [],
        "risk_level": "MEDIUM"
    }
    
    # Check if we have enough data to make a recommendation
    if not scores or "technical" not in scores:
        recommendation["reasoning"].append("Insufficient data for recommendation")
        return recommendation
    
    # Calculate overall score (weighted average)
    weights = {
        "technical": 0.4,
        "sentiment": 0.2,
        "market": 0.2,
        "project": 0.2
    }
    
    # Adjust weights based on available data
    available_categories = [cat for cat in weights.keys() if cat in scores]
    if not available_categories:
        recommendation["reasoning"].append("No analysis data available")
        return recommendation
    
    # Normalize weights based on available data
    total_weight = sum(weights[cat] for cat in available_categories)
    normalized_weights = {cat: weights[cat] / total_weight for cat in available_categories}
    
    # Special handling for 1-hour interval (rapid trading)
    if interval == "1h" and "technical" in scores and "rapid_trading" in scores["technical"]:
        # For 1-hour interval, prioritize rapid trading signals for altcoins
        rapid_trading_score = scores["technical"]["rapid_trading"]
        technical_overall = scores["technical"].get("overall", 0)
        
        # Increase weight of rapid trading signals
        overall_score = 0.6 * rapid_trading_score + 0.4 * technical_overall
        
        if rapid_trading_score > 0.5:
            recommendation["action"] = "STRONG_BUY"
            recommendation["confidence"] = rapid_trading_score
            recommendation["reasoning"].append("Strong rapid trading buy signal detected")
            recommendation["risk_level"] = "HIGH"
        elif rapid_trading_score > 0.3:
            recommendation["action"] = "BUY"
            recommendation["confidence"] = rapid_trading_score
            recommendation["reasoning"].append("Rapid trading buy signal detected")
            recommendation["risk_level"] = "HIGH"
        elif rapid_trading_score < -0.5:
            recommendation["action"] = "STRONG_SELL"
            recommendation["confidence"] = abs(rapid_trading_score)
            recommendation["reasoning"].append("Strong rapid trading sell signal detected")
            recommendation["risk_level"] = "HIGH"
        elif rapid_trading_score < -0.3:
            recommendation["action"] = "SELL"
            recommendation["confidence"] = abs(rapid_trading_score)
            recommendation["reasoning"].append("Rapid trading sell signal detected")
            recommendation["risk_level"] = "HIGH"
    else:
        # Standard analysis for longer timeframes
        overall_score = 0
        for category in available_categories:
            if "overall" in scores[category]:
                overall_score += scores[category]["overall"] * normalized_weights[category]
            else:
                # If overall score not available, use average of available scores
                category_scores = [v for k, v in scores[category].items() if isinstance(v, (int, float))]
                if category_scores:
                    overall_score += (sum(category_scores) / len(category_scores)) * normalized_weights[category]
    
        # Determine action based on overall score
        if overall_score > 0.6:
            recommendation["action"] = "STRONG_BUY"
            recommendation["confidence"] = overall_score
            recommendation["reasoning"].append("Strong positive signals across multiple indicators")
        elif overall_score > 0.3:
            recommendation["action"] = "BUY"
            recommendation["confidence"] = overall_score
            recommendation["reasoning"].append("Positive signals across multiple indicators")
        elif overall_score < -0.6:
            recommendation["action"] = "STRONG_SELL"
            recommendation["confidence"] = abs(overall_score)
            recommendation["reasoning"].append("Strong negative signals across multiple indicators")
        elif overall_score < -0.3:
            recommendation["action"] = "SELL"
            recommendation["confidence"] = abs(overall_score)
            recommendation["reasoning"].append("Negative signals across multiple indicators")
        else:
            recommendation["action"] = "HOLD"
            recommendation["confidence"] = 1 - abs(overall_score) * 2  # Higher confidence for scores closer to 0
            recommendation["reasoning"].append("Mixed or neutral signals")
    
    # Add specific reasoning from each analysis category
    for category, category_scores in scores.items():
        if category == "technical":
            if "trend" in category_scores:
                if category_scores["trend"] > 0.5:
                    recommendation["reasoning"].append("Strong upward trend")
                elif category_scores["trend"] < -0.5:
                    recommendation["reasoning"].append("Strong downward trend")
            
            if "momentum" in category_scores:
                if category_scores["momentum"] > 0.5:
                    recommendation["reasoning"].append("Strong positive momentum")
                elif category_scores["momentum"] < -0.5:
                    recommendation["reasoning"].append("Strong negative momentum")
        
        elif category == "sentiment":
            if "fear_greed" in category_scores:
                if category_scores["fear_greed"] > 0.5:
                    recommendation["reasoning"].append("Market sentiment is greedy")
                elif category_scores["fear_greed"] < -0.5:
                    recommendation["reasoning"].append("Market sentiment is fearful")
        
        elif category == "market":
            if "correlation" in category_scores and category_scores["correlation"] > 0.7:
                recommendation["reasoning"].append("High correlation with market trends")
        
        elif category == "project":
            if "development" in category_scores and category_scores["development"] > 0.7:
                recommendation["reasoning"].append("Strong development activity")
    
    # Determine risk level
    volatility = scores.get("technical", {}).get("volatility", 0)
    if abs(volatility) > 0.7:
        recommendation["risk_level"] = "HIGH"
    elif abs(volatility) < 0.3:
        recommendation["risk_level"] = "LOW"
    else:
        recommendation["risk_level"] = "MEDIUM"
    
    # Limit reasoning to top 5 points
    recommendation["reasoning"] = recommendation["reasoning"][:5]
    
    logger.info(f"Generated recommendation: {recommendation['action']} with confidence {recommendation['confidence']:.2f}")
    return recommendation

def analyze_multiple_cryptocurrencies(symbols: List[str], interval: str = "1d", days: int = 30) -> Dict[str, Dict[str, Any]]:
    """
    Analyze multiple cryptocurrencies and rank them by potential.
    
    Args:
        symbols: List of trading pair symbols
        interval: The time interval for analysis
        days: Number of days of historical data to analyze
        
    Returns:
        Dictionary with analysis results for each cryptocurrency
    """
    logger.info(f"Starting analysis of {len(symbols)} cryptocurrencies")
    
    results = {}
    for symbol in symbols:
        try:
            results[symbol] = analyze_cryptocurrency(symbol, interval, days)
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
    
    logger.info(f"Completed analysis of {len(results)} cryptocurrencies")
    return results

def save_analysis_results(results: Dict[str, Dict[str, Any]], filename: str) -> None:
    """
    Save analysis results to a JSON file.
    
    Args:
        results: Analysis results
        filename: Output filename
    """
    try:
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Saved analysis results to {filename}")
    except Exception as e:
        logger.error(f"Error saving analysis results: {e}")

def load_analysis_results(filename: str) -> Dict[str, Dict[str, Any]]:
    """
    Load analysis results from a JSON file.
    
    Args:
        filename: Input filename
        
    Returns:
        Dictionary with analysis results
    """
    try:
        with open(filename, 'r') as f:
            results = json.load(f)
        logger.info(f"Loaded analysis results from {filename}")
        return results
    except Exception as e:
        logger.error(f"Error loading analysis results: {e}")
        return {}

if __name__ == "__main__":
    # Example usage
    symbols = ["BTC-USD", "ETH-USD", "SOL-USD"]
    results = analyze_multiple_cryptocurrencies(symbols, interval="1h", days=1)
    save_analysis_results(results, "analysis_results.json")


class AnalysisOrchestrator:
    """
    Orchestrator class for cryptocurrency analysis.
    
    This class provides a convenient interface for analyzing cryptocurrencies
    and managing analysis results.
    """
    
    def __init__(self):
        """Initialize the analysis orchestrator."""
        self.logger = logger
    
    def analyze_symbol(self, symbol: str, interval: str = "1h", days: int = 30) -> Optional[Any]:
        """
        Analyze a single cryptocurrency symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTC-USD")
            interval: Time interval for analysis
            days: Number of days of historical data
            
        Returns:
            Analysis result object with signal attribute
        """
        try:
            # Perform comprehensive analysis
            result = analyze_cryptocurrency(symbol, interval, days)
            
            if result and "recommendation" in result:
                # Create a simple result object with signal attribute
                class AnalysisResult:
                    def __init__(self, data):
                        self.signal = data["recommendation"]["action"]
                        self.confidence = data["recommendation"]["confidence"]
                        self.data = data
                
                return AnalysisResult(result)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error analyzing symbol {symbol}: {e}")
            return None
    
    def analyze_multiple_symbols(self, symbols: List[str], interval: str = "1h", days: int = 30) -> Dict[str, Any]:
        """
        Analyze multiple cryptocurrency symbols.
        
        Args:
            symbols: List of trading symbols
            interval: Time interval for analysis
            days: Number of days of historical data
            
        Returns:
            Dictionary mapping symbols to analysis results
        """
        return analyze_multiple_cryptocurrencies(symbols, interval, days)
    
    def save_analysis_results(self, results: Dict[str, Any], filename: str) -> None:
        """
        Save analysis results to a file.
        
        Args:
            results: Analysis results dictionary
            filename: Output filename
        """
        # Convert results to serializable format
        serializable_results = {}
        for symbol, result in results.items():
            if hasattr(result, 'data'):
                serializable_results[symbol] = result.data
            else:
                serializable_results[symbol] = result
        
        save_analysis_results(serializable_results, filename)
    
    def load_analysis_results(self, filename: str) -> Dict[str, Any]:
        """
        Load analysis results from a file.
        
        Args:
            filename: Input filename
            
        Returns:
            Analysis results dictionary
        """
        return load_analysis_results(filename)

