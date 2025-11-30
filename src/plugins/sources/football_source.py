"""
Football (soccer) plugin source using football-data.org API.
"""

import logging

from src.clients.sports.football import FootballClient
from src.models.signage_data import SignageContent
from src.plugins.base_source import BaseSource
from src.plugins.registry import SourceRegistry

logger = logging.getLogger(__name__)


@SourceRegistry.register("football")
class FootballSource(BaseSource):
    """Football (soccer) data source."""

    def validate_config(self) -> bool:
        """Validate football-specific config."""
        # team_id is optional (defaults to Arsenal)
        if "team_id" in self.config:
            if not isinstance(self.config["team_id"], str):
                raise ValueError("team_id must be a string")
        return True

    def fetch_data(self) -> SignageContent | None:
        """Fetch football team data."""
        # Get team_id from config (default to Arsenal: 57)
        team_id = self.config.get("team_id", "57")

        client = FootballClient()
        data = client.get_team_data(team_id)

        if data:
            logger.info(
                f"Football: {data.team_name}, "
                f"Fixtures: {len(data.next_fixtures)}, "
                f"Live: {data.is_live}"
            )
            return data.to_signage()

        return None
