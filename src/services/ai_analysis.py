"""
Central AI Analysis Module using Google Gemini.

This module provides intelligent cryptocurrency market analysis
using Google's Gemini AI model. It serves as the "brain" of the
SaaS application, providing insights and recommendations.
"""

import google.generativeai as genai
from flask import current_app
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests

logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    """Central AI analyzer using Google Gemini."""
    
    def __init__(self, api_key: str):
        """Initialize Gemini analyzer."""
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
    def analyze_market_sentiment(self, symbol: str, market_data: Dict) -> Dict:
        """Analyze market sentiment for a cryptocurrency."""
        try:
            prompt = f"""
            Analyze the market sentiment for {symbol} based on the following data:
            
            Current Price: ${market_data.get('current_price', 'N/A')}
            24h Change: {market_data.get('price_change_24h', 'N/A')}%
            7d Change: {market_data.get('price_change_7d', 'N/A')}%
            Volume 24h: ${market_data.get('volume_24h', 'N/A')}
            Market Cap: ${market_data.get('market_cap', 'N/A')}
            
            Provide a comprehensive sentiment analysis including:
            1. Overall sentiment (Bullish/Bearish/Neutral) with confidence score (0-100)
            2. Key factors influencing the sentiment
            3. Short-term outlook (1-7 days)
            4. Medium-term outlook (1-4 weeks)
            5. Risk assessment
            6. Trading recommendation (Buy/Hold/Sell) with reasoning
            
            Format the response as JSON with the following structure:
            {{
                "sentiment": "Bullish|Bearish|Neutral",
                "confidence": 85,
                "key_factors": ["factor1", "factor2", "factor3"],
                "short_term_outlook": "description",
                "medium_term_outlook": "description",
                "risk_level": "Low|Medium|High",
                "recommendation": "Buy|Hold|Sell",
                "reasoning": "detailed explanation",
                "price_targets": {{
                    "support": 0.0,
                    "resistance": 0.0,
                    "target": 0.0
                }}
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            try:
                analysis = json.loads(response.text)
                analysis['analyzed_at'] = datetime.utcnow().isoformat()
                analysis['symbol'] = symbol
                return analysis
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    'sentiment': 'Neutral',
                    'confidence': 50,
                    'key_factors': ['Analysis parsing error'],
                    'short_term_outlook': response.text[:200],
                    'medium_term_outlook': 'Unable to parse detailed analysis',
                    'risk_level': 'Medium',
                    'recommendation': 'Hold',
                    'reasoning': 'AI response could not be parsed properly',
                    'price_targets': {'support': 0.0, 'resistance': 0.0, 'target': 0.0},
                    'analyzed_at': datetime.utcnow().isoformat(),
                    'symbol': symbol
                }
                
        except Exception as e:
            logger.error(f"Gemini sentiment analysis error for {symbol}: {str(e)}")
            return {
                'sentiment': 'Neutral',
                'confidence': 0,
                'key_factors': ['Analysis unavailable'],
                'short_term_outlook': 'Unable to analyze',
                'medium_term_outlook': 'Unable to analyze',
                'risk_level': 'High',
                'recommendation': 'Hold',
                'reasoning': f'Analysis failed: {str(e)}',
                'price_targets': {'support': 0.0, 'resistance': 0.0, 'target': 0.0},
                'analyzed_at': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'error': True
            }
    
    def analyze_technical_indicators(self, symbol: str, price_data: List[Dict]) -> Dict:
        """Analyze technical indicators using AI."""
        try:
            # Prepare price data summary
            if not price_data:
                raise ValueError("No price data provided")
            
            recent_prices = [float(p.get('close', 0)) for p in price_data[-20:]]  # Last 20 data points
            price_summary = {
                'current': recent_prices[-1] if recent_prices else 0,
                'high_20': max(recent_prices) if recent_prices else 0,
                'low_20': min(recent_prices) if recent_prices else 0,
                'avg_20': sum(recent_prices) / len(recent_prices) if recent_prices else 0
            }
            
            prompt = f"""
            Analyze the technical indicators for {symbol} based on recent price action:
            
            Current Price: ${price_summary['current']}
            20-period High: ${price_summary['high_20']}
            20-period Low: ${price_summary['low_20']}
            20-period Average: ${price_summary['avg_20']:.2f}
            
            Recent price trend: {recent_prices[-10:] if len(recent_prices) >= 10 else recent_prices}
            
            Provide technical analysis including:
            1. Trend direction (Uptrend/Downtrend/Sideways)
            2. Momentum assessment
            3. Support and resistance levels
            4. Key technical patterns identified
            5. RSI interpretation (estimate based on price action)
            6. Moving average analysis
            7. Trading signals
            
            Format as JSON:
            {{
                "trend_direction": "Uptrend|Downtrend|Sideways",
                "momentum": "Strong|Moderate|Weak",
                "support_level": 0.0,
                "resistance_level": 0.0,
                "patterns": ["pattern1", "pattern2"],
                "rsi_estimate": 50,
                "ma_signal": "Bullish|Bearish|Neutral",
                "trading_signals": ["signal1", "signal2"],
                "strength_score": 75
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            try:
                analysis = json.loads(response.text)
                analysis['analyzed_at'] = datetime.utcnow().isoformat()
                analysis['symbol'] = symbol
                analysis['data_points'] = len(price_data)
                return analysis
            except json.JSONDecodeError:
                return {
                    'trend_direction': 'Sideways',
                    'momentum': 'Moderate',
                    'support_level': price_summary['low_20'],
                    'resistance_level': price_summary['high_20'],
                    'patterns': ['Unable to parse'],
                    'rsi_estimate': 50,
                    'ma_signal': 'Neutral',
                    'trading_signals': ['Analysis parsing error'],
                    'strength_score': 50,
                    'analyzed_at': datetime.utcnow().isoformat(),
                    'symbol': symbol,
                    'data_points': len(price_data)
                }
                
        except Exception as e:
            logger.error(f"Gemini technical analysis error for {symbol}: {str(e)}")
            return {
                'trend_direction': 'Sideways',
                'momentum': 'Weak',
                'support_level': 0.0,
                'resistance_level': 0.0,
                'patterns': ['Analysis unavailable'],
                'rsi_estimate': 50,
                'ma_signal': 'Neutral',
                'trading_signals': ['Analysis failed'],
                'strength_score': 0,
                'analyzed_at': datetime.utcnow().isoformat(),
                'symbol': symbol,
                'error': True
            }
    
    def generate_portfolio_recommendations(self, user_portfolio: Dict, market_data: Dict) -> Dict:
        """Generate AI-powered portfolio recommendations."""
        try:
            prompt = f"""
            Analyze this cryptocurrency portfolio and provide optimization recommendations:
            
            Current Portfolio:
            {json.dumps(user_portfolio, indent=2)}
            
            Current Market Data:
            {json.dumps(market_data, indent=2)}
            
            Provide comprehensive portfolio analysis including:
            1. Portfolio diversification score (0-100)
            2. Risk assessment
            3. Rebalancing recommendations
            4. Position sizing suggestions
            5. Entry/exit strategies
            6. Risk management advice
            7. Performance optimization tips
            
            Format as JSON:
            {{
                "diversification_score": 75,
                "risk_level": "Medium",
                "rebalancing_needed": true,
                "recommendations": [
                    {{
                        "action": "Buy|Sell|Hold",
                        "symbol": "BTC",
                        "percentage": 25,
                        "reasoning": "explanation"
                    }}
                ],
                "risk_management": ["tip1", "tip2"],
                "optimization_tips": ["tip1", "tip2"],
                "overall_score": 80
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            try:
                analysis = json.loads(response.text)
                analysis['analyzed_at'] = datetime.utcnow().isoformat()
                return analysis
            except json.JSONDecodeError:
                return {
                    'diversification_score': 50,
                    'risk_level': 'Medium',
                    'rebalancing_needed': False,
                    'recommendations': [],
                    'risk_management': ['Unable to parse recommendations'],
                    'optimization_tips': ['Analysis parsing error'],
                    'overall_score': 50,
                    'analyzed_at': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Gemini portfolio analysis error: {str(e)}")
            return {
                'diversification_score': 0,
                'risk_level': 'High',
                'rebalancing_needed': False,
                'recommendations': [],
                'risk_management': ['Analysis unavailable'],
                'optimization_tips': ['Portfolio analysis failed'],
                'overall_score': 0,
                'analyzed_at': datetime.utcnow().isoformat(),
                'error': True
            }
    
    def analyze_market_trends(self, symbols: List[str], timeframe: str = '24h') -> Dict:
        """Analyze overall market trends across multiple cryptocurrencies."""
        try:
            prompt = f"""
            Analyze the overall cryptocurrency market trends for the following assets:
            {', '.join(symbols)}
            
            Timeframe: {timeframe}
            
            Provide market-wide analysis including:
            1. Overall market sentiment
            2. Sector performance (DeFi, Layer 1, etc.)
            3. Market correlation analysis
            4. Volatility assessment
            5. Institutional activity indicators
            6. Market cycle position
            7. Key market drivers
            
            Format as JSON:
            {{
                "market_sentiment": "Bullish|Bearish|Neutral",
                "market_phase": "Accumulation|Markup|Distribution|Decline",
                "volatility": "High|Medium|Low",
                "correlation_strength": "High|Medium|Low",
                "institutional_flow": "Inflow|Outflow|Neutral",
                "key_drivers": ["driver1", "driver2"],
                "sector_performance": {{
                    "defi": "Outperforming|Underperforming|Neutral",
                    "layer1": "Outperforming|Underperforming|Neutral",
                    "meme": "Outperforming|Underperforming|Neutral"
                }},
                "market_score": 75
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            try:
                analysis = json.loads(response.text)
                analysis['analyzed_at'] = datetime.utcnow().isoformat()
                analysis['symbols_analyzed'] = symbols
                analysis['timeframe'] = timeframe
                return analysis
            except json.JSONDecodeError:
                return {
                    'market_sentiment': 'Neutral',
                    'market_phase': 'Accumulation',
                    'volatility': 'Medium',
                    'correlation_strength': 'Medium',
                    'institutional_flow': 'Neutral',
                    'key_drivers': ['Analysis parsing error'],
                    'sector_performance': {
                        'defi': 'Neutral',
                        'layer1': 'Neutral',
                        'meme': 'Neutral'
                    },
                    'market_score': 50,
                    'analyzed_at': datetime.utcnow().isoformat(),
                    'symbols_analyzed': symbols,
                    'timeframe': timeframe
                }
                
        except Exception as e:
            logger.error(f"Gemini market trends analysis error: {str(e)}")
            return {
                'market_sentiment': 'Neutral',
                'market_phase': 'Accumulation',
                'volatility': 'High',
                'correlation_strength': 'Medium',
                'institutional_flow': 'Neutral',
                'key_drivers': ['Analysis unavailable'],
                'sector_performance': {
                    'defi': 'Neutral',
                    'layer1': 'Neutral',
                    'meme': 'Neutral'
                },
                'market_score': 0,
                'analyzed_at': datetime.utcnow().isoformat(),
                'symbols_analyzed': symbols,
                'timeframe': timeframe,
                'error': True
            }


def get_gemini_analyzer() -> Optional[GeminiAnalyzer]:
    """Get Gemini analyzer instance."""
    try:
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            logger.warning("Gemini API key not configured")
            return None
        
        return GeminiAnalyzer(api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Gemini analyzer: {str(e)}")
        return None


def fetch_market_data(symbol: str) -> Dict:
    """Fetch basic market data for a cryptocurrency."""
    try:
        # Using CoinGecko API for market data
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {
            'ids': symbol.lower(),
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_7d_change': 'true',
            'include_market_cap': 'true',
            'include_24hr_vol': 'true'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if symbol.lower() in data:
            coin_data = data[symbol.lower()]
            return {
                'current_price': coin_data.get('usd', 0),
                'price_change_24h': coin_data.get('usd_24h_change', 0),
                'price_change_7d': coin_data.get('usd_7d_change', 0),
                'market_cap': coin_data.get('usd_market_cap', 0),
                'volume_24h': coin_data.get('usd_24h_vol', 0)
            }
        else:
            return {}
            
    except Exception as e:
        logger.error(f"Failed to fetch market data for {symbol}: {str(e)}")
        return {}


def get_comprehensive_analysis(symbol: str, user_id: int) -> Dict:
    """Get comprehensive AI analysis for a cryptocurrency."""
    try:
        analyzer = get_gemini_analyzer()
        if not analyzer:
            return {'error': 'AI analysis unavailable'}
        
        # Fetch market data
        market_data = fetch_market_data(symbol)
        if not market_data:
            return {'error': f'Market data unavailable for {symbol}'}
        
        # Perform AI analysis
        sentiment_analysis = analyzer.analyze_market_sentiment(symbol, market_data)
        
        # Combine results
        comprehensive_analysis = {
            'symbol': symbol,
            'market_data': market_data,
            'ai_analysis': sentiment_analysis,
            'analyzed_at': datetime.utcnow().isoformat(),
            'user_id': user_id
        }
        
        return comprehensive_analysis
        
    except Exception as e:
        logger.error(f"Comprehensive analysis error for {symbol}: {str(e)}")
        return {
            'error': f'Analysis failed: {str(e)}',
            'symbol': symbol,
            'analyzed_at': datetime.utcnow().isoformat()
        }

