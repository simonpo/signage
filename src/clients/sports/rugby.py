"""
Rugby client using mock data for England Men's Rugby.
TODO: Replace with proper web scraping or API when available.
"""

import logging

from src.clients.sports.base_sports import BaseSportsClient
from src.models.signage_data import SportsData, SportsFixture, SportsResult

logger = logging.getLogger(__name__)


class RugbyClient(BaseSportsClient):
    """
    Rugby client for England Men's Rugby.

    Currently uses mock data. Future: scrape England Rugby website or use API.
    Website: https://www.englandrugby.com/fixtures-and-results/
    """

    def __init__(self):
        """Initialize rugby client."""
        super().__init__()

    def get_team_data(self, team_id: str = "2") -> SportsData | None:
        """
        Get comprehensive team data including fixtures and results.

        Args:
            team_id: Team ID (default "2" for England Men)

        Returns:
            SportsData object with mock data
        """
        try:
            # Mock last result (realistic Six Nations data)
            last_result = SportsResult(
                home_team="Ireland",
                away_team="England",
                home_score="17",
                away_score="13",
                date="Feb 8",
                competition="Six Nations",
            )

            # Mock upcoming fixtures (realistic international rugby)
            next_fixtures = [
                SportsFixture(
                    home_team="England",
                    away_team="France",
                    date="Mar 15, 7:45 AM PST",
                    competition="Six Nations",
                    venue="Twickenham Stadium",
                ),
                SportsFixture(
                    home_team="England",
                    away_team="Italy",
                    date="Mar 22, 7:00 AM PST",
                    competition="Six Nations",
                    venue="Stadio Olimpico",
                ),
                SportsFixture(
                    home_team="Wales",
                    away_team="England",
                    date="Mar 29, 7:00 AM PST",
                    competition="Six Nations",
                    venue="Principality Stadium",
                ),
            ]

            return SportsData(
                team_name="England",
                sport="rugby",
                last_result=last_result,
                next_fixtures=next_fixtures,
                league_table=[],  # No league table for international rugby
                is_live=False,
                live_score=None,
                primary_color="#FFFFFF",  # England white
                secondary_color="#C8102E",  # England red
            )

        except Exception as e:
            logger.error(f"Failed to get rugby data: {e}")
            return None

    def is_game_today(self, team_id: str = "2") -> bool:
        """Check if team has a match today."""
        # Mock implementation
        return False

    def is_game_live(self, team_id: str = "2") -> bool:
        """Check if team has a live match."""
        # Mock implementation
        return False
