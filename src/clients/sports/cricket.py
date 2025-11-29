"""
Cricket client stub.
TODO: Implement using Cricbuzz or CricketAPI.
"""

import logging

from src.clients.sports.base_sports import BaseSportsClient
from src.models.signage_data import SportsData

logger = logging.getLogger(__name__)


class CricketClient(BaseSportsClient):
    """
    Cricket client for England national team.

    Recommended APIs:
    - Cricbuzz unofficial API
    - CricketAPI (https://www.cricketapi.com)
    - ESPN Cricinfo (unofficial)
    """

    def __init__(self):
        """Initialize cricket client."""
        super().__init__()
        logger.warning("CricketClient not yet implemented")

    def get_team_data(self, team_id: str) -> SportsData | None:
        """Get team data (not implemented)."""
        logger.warning("CricketClient.get_team_data() not yet implemented")
        return None

    def is_game_today(self, team_id: str) -> bool:
        """Check if match today (not implemented)."""
        return False

    def is_game_live(self, team_id: str) -> bool:
        """Check if match live (not implemented)."""
        return False
