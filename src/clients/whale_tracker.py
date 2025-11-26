"""
Whale sighting tracker using web scraping.
Fetches recent whale sightings from the Whale Museum.
"""

import logging
from typing import Optional

from src.clients.base import APIClient
from src.config import Config
from src.models.signage_data import WhaleData

logger = logging.getLogger(__name__)


class WhaleTrackerClient(APIClient):
    """
    Client for whale sighting data.
    Uses web scraping since no official API exists.
    """

    def __init__(self):
        """Initialize with whale tracker URL."""
        super().__init__()
        self.url = Config.WHALE_TRACKER_URL

    def get_sightings(self) -> Optional[WhaleData]:
        """
        Fetch recent whale sightings.

        Returns:
            WhaleData object or None on failure
        """
        logger.warning(
            "Whale tracker scraping not yet implemented - " "HTML structure needs to be analyzed"
        )

        # TODO: Implement actual scraping
        # Steps:
        # 1. Fetch page with self._make_request()
        # 2. Parse HTML with BeautifulSoup
        # 3. Extract sighting data (date, species, location)
        # 4. Return WhaleData with sightings list

        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.error("BeautifulSoup not installed: pip install beautifulsoup4")
            return None

        response = self._make_request(self.url)

        if not response:
            logger.error("Failed to fetch whale sightings page")
            return None

        # Stub implementation
        return WhaleData(sightings=[], last_sighting_date=None)

        # TODO: Replace with actual parsing:
        # soup = BeautifulSoup(response.text, 'html.parser')
        # sightings = []
        #
        # for sighting_element in soup.select('.sighting-class'):
        #     sightings.append({
        #         'date': ...,
        #         'species': ...,
        #         'location': ...,
        #     })
        #
        # return WhaleData(
        #     sightings=sightings,
        #     last_sighting_date=sightings[0]['date'] if sightings else None
        # )
