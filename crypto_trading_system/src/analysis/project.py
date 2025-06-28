"""
Project fundamentals analysis module for cryptocurrency trading.
"""

from typing import Dict, List, Optional, Union, Any
from datetime import datetime

from ..models.data_models import ProjectData
from ..utils.helpers import logger
from ..api.clients import CoinGeckoClient
from ..config import settings

class ProjectAnalyzer:
    """
    Class for analyzing project fundamentals data related to cryptocurrencies.
    """
    
    def __init__(self):
        """Initialize the project analyzer."""
        self.coingecko_client = CoinGeckoClient()
    
    def get_project_data(self, coin_id: str) -> Optional[ProjectData]:
        """
        Get project fundamental data for a coin.
        
        Args:
            coin_id: CoinGecko coin ID (e.g., "bitcoin")
            
        Returns:
            ProjectData object or None if an error occurred
        """
        try:
            # Get detailed coin data from CoinGecko
            coin_data = self.coingecko_client.get_coin_data(coin_id)
            
            if not coin_data:
                logger.warning(f"Failed to get project data for {coin_id}")
                return None
            
            # Extract developer and community data
            developer_data = coin_data.get("developer_data", {})
            community_data = coin_data.get("community_data", {})
            
            # Calculate developer score
            developer_score = self._calculate_developer_score(developer_data)
            
            # Calculate community score
            community_score = self._calculate_community_score(community_data)
            
            # Get liquidity score if available
            liquidity_score = coin_data.get("liquidity_score")
            
            # Get public interest score if available
            public_interest_score = coin_data.get("public_interest_score")
            
            return ProjectData(
                timestamp=datetime.now(),
                coin_id=coin_id,
                developer_score=developer_score,
                community_score=community_score,
                liquidity_score=liquidity_score,
                public_interest_score=public_interest_score
            )
        except Exception as e:
            logger.error(f"Error getting project data for {coin_id}: {e}")
            return None
    
    def _calculate_developer_score(self, developer_data: Dict) -> float:
        """
        Calculate a developer activity score based on GitHub metrics.
        
        Args:
            developer_data: Developer data from CoinGecko
            
        Returns:
            Developer score (0.0 to 1.0)
        """
        if not developer_data:
            return 0.0
        
        # Extract relevant metrics
        commits_4_weeks = developer_data.get("commit_count_4_weeks", 0) or 0
        stars = developer_data.get("stars", 0) or 0
        forks = developer_data.get("forks", 0) or 0
        subscribers = developer_data.get("subscribers", 0) or 0
        total_issues = developer_data.get("total_issues", 0) or 0
        closed_issues = developer_data.get("closed_issues", 0) or 0
        
        # Calculate issue resolution rate
        issue_resolution_rate = 0.0
        if total_issues > 0:
            issue_resolution_rate = closed_issues / total_issues
        
        # Normalize metrics
        norm_commits = min(commits_4_weeks / 100.0, 1.0)  # Cap at 100 commits
        norm_stars = min(stars / 10000.0, 1.0)  # Cap at 10,000 stars
        norm_forks = min(forks / 5000.0, 1.0)  # Cap at 5,000 forks
        
        # Weighted score calculation
        score = (
            0.5 * norm_commits +  # Recent activity is most important
            0.2 * norm_stars +
            0.2 * norm_forks +
            0.1 * issue_resolution_rate
        )
        
        return min(score, 1.0)  # Cap at 1.0
    
    def _calculate_community_score(self, community_data: Dict) -> float:
        """
        Calculate a community engagement score based on social metrics.
        
        Args:
            community_data: Community data from CoinGecko
            
        Returns:
            Community score (0.0 to 1.0)
        """
        if not community_data:
            return 0.0
        
        # Extract relevant metrics
        reddit_subscribers = community_data.get("reddit_subscribers", 0) or 0
        reddit_active_accounts = community_data.get("reddit_accounts_active_48h", 0) or 0
        twitter_followers = community_data.get("twitter_followers", 0) or 0
        telegram_users = community_data.get("telegram_channel_user_count", 0) or 0
        
        # Normalize metrics
        norm_reddit_subs = min(reddit_subscribers / 1000000.0, 1.0)  # Cap at 1M subscribers
        norm_reddit_active = 0.0
        if reddit_subscribers > 0:
            norm_reddit_active = min(reddit_active_accounts / (reddit_subscribers * 0.05), 1.0)  # Expect 5% active
        norm_twitter = min(twitter_followers / 1000000.0, 1.0)  # Cap at 1M followers
        norm_telegram = min(telegram_users / 100000.0, 1.0)  # Cap at 100K users
        
        # Weighted score calculation
        score = (
            0.3 * norm_reddit_subs +
            0.3 * norm_twitter +
            0.2 * norm_reddit_active +
            0.2 * norm_telegram
        )
        
        return min(score, 1.0)  # Cap at 1.0
    
    def score_developer_activity(self, developer_score: Optional[float]) -> int:
        """
        Convert normalized developer score to integer score.
        
        Args:
            developer_score: Normalized developer score (0.0 to 1.0)
            
        Returns:
            Score from -2 to +2
        """
        if developer_score is None:
            return 0
        
        # Very high developer activity
        if developer_score > 0.8:
            return 2
        # High developer activity
        elif developer_score > 0.6:
            return 1
        # Low developer activity
        elif developer_score < 0.3:
            return -1
        # Very low developer activity
        elif developer_score < 0.1:
            return -2
        # Average developer activity
        else:
            return 0
    
    def score_community_engagement(self, community_score: Optional[float]) -> int:
        """
        Convert normalized community score to integer score.
        
        Args:
            community_score: Normalized community score (0.0 to 1.0)
            
        Returns:
            Score from -2 to +2
        """
        if community_score is None:
            return 0
        
        # Very high community engagement
        if community_score > 0.8:
            return 2
        # High community engagement
        elif community_score > 0.6:
            return 1
        # Low community engagement
        elif community_score < 0.3:
            return -1
        # Very low community engagement
        elif community_score < 0.1:
            return -2
        # Average community engagement
        else:
            return 0


def analyze_project(symbol: str, interval: str = "1d") -> Dict[str, float]:
    """
    Analyze project fundamentals for a cryptocurrency symbol.
    
    Args:
        symbol: Trading symbol (e.g., "BTC-USD")
        interval: Time interval for analysis
        
    Returns:
        Dictionary containing project analysis scores
    """
    analyzer = ProjectAnalyzer()
    
    try:
        # Convert symbol to coin ID (remove -USD suffix)
        coin_id = symbol.replace("-USD", "").lower()
        if coin_id == "btc":
            coin_id = "bitcoin"
        elif coin_id == "eth":
            coin_id = "ethereum"
        
        # Get project data
        project_data = analyzer.get_project_data(coin_id)
        
        if not project_data:
            logger.warning(f"Failed to get project data for {symbol}")
            return {
                "developer_score": 0.0,
                "community_score": 0.0,
                "overall_project_score": 0.0
            }
        
        # Calculate scores
        developer_score = analyzer.score_developer_activity(project_data.developer_score)
        community_score = analyzer.score_community_engagement(project_data.community_score)
        
        # Calculate overall project score (weighted average)
        overall_score = (
            developer_score * 0.6 +
            community_score * 0.4
        )
        
        return {
            "developer_score": float(developer_score),
            "community_score": float(community_score),
            "overall_project_score": float(overall_score)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing project data for {symbol}: {e}")
        return {
            "developer_score": 0.0,
            "community_score": 0.0,
            "overall_project_score": 0.0
        }

