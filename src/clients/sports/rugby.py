"""
Rugby client stub.
TODO: Implement using TheSportsDB or ESPN Rugby API.
"""

import logging
from typing import Optional

from src.clients.sports.base_sports import BaseSportsClient
from src.models.signage_data import SportsData

logger = logging.getLogger(__name__)


class RugbyClient(BaseSportsClient):
    """
    Rugby client for Six Nations and Premiership Rugby.
    
    Recommended APIs:
    - TheSportsDB (https://www.thesportsdb.com/api.php)
    - ESPN Rugby API (similar structure to NFL)
    """
    
    def __init__(self):
        """Initialize rugby client."""
        super().__init__()
        logger.warning("RugbyClient not yet implemented")
    
    def get_team_data(self, team_id: str) -> Optional[SportsData]:
        """Get team data (not implemented)."""
        logger.warning("RugbyClient.get_team_data() not yet implemented")
        return None
    
    def is_game_today(self, team_id: str) -> bool:
        """Check if match today (not implemented)."""
        return False
    
    def is_game_live(self, team_id: str) -> bool:
        """Check if match live (not implemented)."""
        return False
