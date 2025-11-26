"""
Base sports client with live detection and caching.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional

from src.clients.base import APIClient
from src.models.signage_data import SportsData

logger = logging.getLogger(__name__)


class BaseSportsClient(APIClient, ABC):
    """
    Base class for all sports API clients.
    Handles caching and live game detection.
    """

    # How long to cache sports data (in minutes)
    cache_duration_minutes = 15

    @abstractmethod
    def get_team_data(self, team_id: str) -> Optional[SportsData]:
        """
        Fetch comprehensive team data.

        Args:
            team_id: Team identifier (API-specific)

        Returns:
            SportsData object or None on failure
        """
        pass

    @abstractmethod
    def is_game_today(self, team_id: str) -> bool:
        """
        Check if team has a game today.

        Args:
            team_id: Team identifier

        Returns:
            True if game is scheduled today
        """
        pass

    @abstractmethod
    def is_game_live(self, team_id: str) -> bool:
        """
        Check if team is currently playing.

        Args:
            team_id: Team identifier

        Returns:
            True if game is live right now
        """
        pass

    def should_update_frequently(self, team_id: str) -> bool:
        """
        Determine if this team needs frequent updates.
        Returns True if game is today or currently live.

        Args:
            team_id: Team identifier

        Returns:
            True if frequent updates needed
        """
        return self.is_game_today(team_id) or self.is_game_live(team_id)
