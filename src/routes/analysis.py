"""
AI Analysis routes for the SaaS application.

This module provides endpoints for AI-powered cryptocurrency analysis
using the central Gemini AI service.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from src.services.ai_analysis import get_comprehensive_analysis, get_gemini_analyzer, fetch_market_data
from src.models.user import AnalysisCache, db
from src.routes.api_keys import get_user_api_credentials
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analyze/<symbol>', methods=['GET'])
@login_required
def analyze_symbol(symbol):
    """Get AI analysis for a specific cryptocurrency symbol."""
    try:
        symbol = symbol.upper()
        
        # Check for cached analysis (valid for 1 hour)
        cached_analysis = AnalysisCache.query.filter_by(
            user_id=current_user.id,
            symbol=symbol,
            analysis_type='comprehensive'
        ).filter(
            AnalysisCache.expires_at > datetime.utcnow()
        ).first()
        
        if cached_analysis and not cached_analysis.is_expired():
            logger.info(f"Returning cached analysis for {symbol}, user {current_user.id}")
            return jsonify({
                'analysis': cached_analysis.analysis_data,
                'cached': True,
                'cache_expires_at': cached_analysis.expires_at.isoformat()
            }), 200
        
        # Get fresh analysis
        analysis = get_comprehensive_analysis(symbol, current_user.id)
        
        if 'error' in analysis:
            return jsonify(analysis), 400
        
        # Cache the analysis
        try:
            # Remove old cache entries for this symbol
            AnalysisCache.query.filter_by(
                user_id=current_user.id,
                symbol=symbol,
                analysis_type='comprehensive'
            ).delete()
            
            # Create new cache entry
            cache_entry = AnalysisCache(
                user_id=current_user.id,
                symbol=symbol,
                timeframe='1h',
                analysis_type='comprehensive',
                analysis_data=analysis,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            
            db.session.add(cache_entry)
            db.session.commit()
            
        except Exception as cache_error:
            logger.warning(f"Failed to cache analysis: {str(cache_error)}")
            # Continue without caching
        
        return jsonify({
            'analysis': analysis,
            'cached': False
        }), 200
        
    except Exception as e:
        logger.error(f"Analysis error for {symbol}, user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Analysis failed'}), 500

@analysis_bp.route('/analyze/batch', methods=['POST'])
@login_required
def analyze_batch():
    """Analyze multiple cryptocurrency symbols."""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])
        
        if not symbols or len(symbols) > 10:  # Limit to 10 symbols
            return jsonify({'error': 'Please provide 1-10 symbols'}), 400
        
        results = {}
        
        for symbol in symbols:
            symbol = symbol.upper()
            try:
                # Check cache first
                cached_analysis = AnalysisCache.query.filter_by(
                    user_id=current_user.id,
                    symbol=symbol,
                    analysis_type='comprehensive'
                ).filter(
                    AnalysisCache.expires_at > datetime.utcnow()
                ).first()
                
                if cached_analysis and not cached_analysis.is_expired():
                    results[symbol] = {
                        'analysis': cached_analysis.analysis_data,
                        'cached': True
                    }
                else:
                    # Get fresh analysis
                    analysis = get_comprehensive_analysis(symbol, current_user.id)
                    results[symbol] = {
                        'analysis': analysis,
                        'cached': False
                    }
                    
                    # Cache if successful
                    if 'error' not in analysis:
                        try:
                            AnalysisCache.query.filter_by(
                                user_id=current_user.id,
                                symbol=symbol,
                                analysis_type='comprehensive'
                            ).delete()
                            
                            cache_entry = AnalysisCache(
                                user_id=current_user.id,
                                symbol=symbol,
                                timeframe='1h',
                                analysis_type='comprehensive',
                                analysis_data=analysis,
                                expires_at=datetime.utcnow() + timedelta(hours=1)
                            )
                            
                            db.session.add(cache_entry)
                            
                        except Exception as cache_error:
                            logger.warning(f"Failed to cache analysis for {symbol}: {str(cache_error)}")
                            
            except Exception as symbol_error:
                logger.error(f"Analysis error for {symbol}: {str(symbol_error)}")
                results[symbol] = {
                    'analysis': {'error': f'Analysis failed for {symbol}'},
                    'cached': False
                }
        
        # Commit all cache entries
        try:
            db.session.commit()
        except Exception as commit_error:
            logger.warning(f"Failed to commit cache entries: {str(commit_error)}")
            db.session.rollback()
        
        return jsonify({
            'results': results,
            'analyzed_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Batch analysis error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Batch analysis failed'}), 500

@analysis_bp.route('/market-overview', methods=['GET'])
@login_required
def market_overview():
    """Get AI-powered market overview."""
    try:
        # Default symbols for market overview
        symbols = ['bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot']
        
        analyzer = get_gemini_analyzer()
        if not analyzer:
            return jsonify({'error': 'AI analysis unavailable'}), 503
        
        # Check for cached market overview
        cached_overview = AnalysisCache.query.filter_by(
            user_id=current_user.id,
            symbol='MARKET_OVERVIEW',
            analysis_type='market_trends'
        ).filter(
            AnalysisCache.expires_at > datetime.utcnow()
        ).first()
        
        if cached_overview and not cached_overview.is_expired():
            return jsonify({
                'overview': cached_overview.analysis_data,
                'cached': True,
                'cache_expires_at': cached_overview.expires_at.isoformat()
            }), 200
        
        # Get fresh market analysis
        market_analysis = analyzer.analyze_market_trends(symbols, '24h')
        
        # Cache the overview
        try:
            AnalysisCache.query.filter_by(
                user_id=current_user.id,
                symbol='MARKET_OVERVIEW',
                analysis_type='market_trends'
            ).delete()
            
            cache_entry = AnalysisCache(
                user_id=current_user.id,
                symbol='MARKET_OVERVIEW',
                timeframe='24h',
                analysis_type='market_trends',
                analysis_data=market_analysis,
                expires_at=datetime.utcnow() + timedelta(hours=2)  # Cache for 2 hours
            )
            
            db.session.add(cache_entry)
            db.session.commit()
            
        except Exception as cache_error:
            logger.warning(f"Failed to cache market overview: {str(cache_error)}")
        
        return jsonify({
            'overview': market_analysis,
            'cached': False
        }), 200
        
    except Exception as e:
        logger.error(f"Market overview error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Market overview failed'}), 500

@analysis_bp.route('/portfolio-analysis', methods=['POST'])
@login_required
def portfolio_analysis():
    """Analyze user's portfolio with AI recommendations."""
    try:
        data = request.get_json()
        portfolio = data.get('portfolio', {})
        
        if not portfolio:
            return jsonify({'error': 'Portfolio data required'}), 400
        
        analyzer = get_gemini_analyzer()
        if not analyzer:
            return jsonify({'error': 'AI analysis unavailable'}), 503
        
        # Get market data for portfolio assets
        market_data = {}
        for symbol in portfolio.keys():
            market_data[symbol] = fetch_market_data(symbol)
        
        # Generate AI recommendations
        recommendations = analyzer.generate_portfolio_recommendations(portfolio, market_data)
        
        return jsonify({
            'recommendations': recommendations,
            'portfolio': portfolio,
            'market_data': market_data,
            'analyzed_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Portfolio analysis error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Portfolio analysis failed'}), 500

@analysis_bp.route('/cache', methods=['GET'])
@login_required
def get_analysis_cache():
    """Get user's cached analyses."""
    try:
        cache_entries = AnalysisCache.query.filter_by(
            user_id=current_user.id
        ).filter(
            AnalysisCache.expires_at > datetime.utcnow()
        ).order_by(AnalysisCache.created_at.desc()).limit(20).all()
        
        return jsonify({
            'cache_entries': [entry.to_dict() for entry in cache_entries]
        }), 200
        
    except Exception as e:
        logger.error(f"Get cache error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Failed to get cache'}), 500

@analysis_bp.route('/cache/<int:cache_id>', methods=['DELETE'])
@login_required
def delete_cache_entry(cache_id):
    """Delete a specific cache entry."""
    try:
        cache_entry = AnalysisCache.query.filter_by(
            id=cache_id,
            user_id=current_user.id
        ).first()
        
        if not cache_entry:
            return jsonify({'error': 'Cache entry not found'}), 404
        
        db.session.delete(cache_entry)
        db.session.commit()
        
        return jsonify({'message': 'Cache entry deleted'}), 200
        
    except Exception as e:
        logger.error(f"Delete cache error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Failed to delete cache entry'}), 500

@analysis_bp.route('/cache/clear', methods=['DELETE'])
@login_required
def clear_analysis_cache():
    """Clear all cached analyses for the user."""
    try:
        deleted_count = AnalysisCache.query.filter_by(
            user_id=current_user.id
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'message': f'Cleared {deleted_count} cache entries'
        }), 200
        
    except Exception as e:
        logger.error(f"Clear cache error for user {current_user.id}: {str(e)}")
        return jsonify({'error': 'Failed to clear cache'}), 500

@analysis_bp.route('/supported-symbols', methods=['GET'])
def get_supported_symbols():
    """Get list of supported cryptocurrency symbols."""
    # Popular cryptocurrencies supported by the analysis
    symbols = [
        {'symbol': 'BTC', 'name': 'Bitcoin', 'id': 'bitcoin'},
        {'symbol': 'ETH', 'name': 'Ethereum', 'id': 'ethereum'},
        {'symbol': 'SOL', 'name': 'Solana', 'id': 'solana'},
        {'symbol': 'ADA', 'name': 'Cardano', 'id': 'cardano'},
        {'symbol': 'DOT', 'name': 'Polkadot', 'id': 'polkadot'},
        {'symbol': 'LINK', 'name': 'Chainlink', 'id': 'chainlink'},
        {'symbol': 'MATIC', 'name': 'Polygon', 'id': 'matic-network'},
        {'symbol': 'AVAX', 'name': 'Avalanche', 'id': 'avalanche-2'},
        {'symbol': 'ATOM', 'name': 'Cosmos', 'id': 'cosmos'},
        {'symbol': 'ALGO', 'name': 'Algorand', 'id': 'algorand'}
    ]
    
    return jsonify({'symbols': symbols}), 200

