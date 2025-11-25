"""
Football (soccer) client stub.
TODO: Implement using football-data.org or API-Football.
"""

import logging
from typing import Optional

from src.clients.sports.base_sports import BaseSportsClient
from src.models.signage_data import SportsData

logger = logging.getLogger(__name__)


class FootballClient(BaseSportsClient):
    """
    Football (soccer) client for Premier League.
    
    Recommended APIs:
    - https://www.football-data.org (free tier available)
    - https://www.api-football.com (RapidAPI)
    """
    
    def __init__(self):
        """Initialize football client."""
        super().__init__()
        logger.warning("FootballClient not yet implemented")
    
    def get_team_data(self, team_id: str) -> Optional[SportsData]:
        """Get team data (not implemented)."""
        logger.warning("FootballClient.get_team_data() not yet implemented")
        return None
    
    def is_game_today(self, team_id: str) -> bool:
        """Check if game today (not implemented)."""
        return False
    
    def is_game_live(self, team_id: str) -> bool:
        """Check if game live (not implemented)."""
        return False
