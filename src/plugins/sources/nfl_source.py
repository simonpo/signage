"""
NFL source plugin using ESPN API.
"""

import logging

from src.clients.sports.nfl import NFLClient
from src.models.signage_data import SignageContent
from src.plugins.base_source import BaseSource
from src.plugins.registry import SourceRegistry

logger = logging.getLogger(__name__)


@SourceRegistry.register("nfl")
class NFLSource(BaseSource):
    """Source for NFL team data using ESPN API."""

    def validate_config(self) -> bool:
        """Validate NFL-specific config."""
        if "team_id" not in self.config:
            raise ValueError("team_id is required for NFL source")

        if not isinstance(self.config["team_id"], str):
            raise ValueError("team_id must be a string")

        return True

    def fetch_data(self) -> SignageContent | None:
        """
        Fetch NFL team data and convert to SignageContent.

        Returns:
            SignageContent with metadata, or None on failure
        """
        team_id = self.config["team_id"]

        client = NFLClient()
        data = client.get_team_data(team_id)

        if data:
            logger.info(
                f"NFL: {data.team_name}, "
                f"Fixtures: {len(data.next_fixtures)}, "
                f"Live: {data.is_live}"
            )
            return data.to_signage()

        logger.error(f"Failed to fetch NFL data for team {team_id}")
        return None
