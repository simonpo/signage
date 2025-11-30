"""
Ferry map data source plugin.
Wraps FerryClient for full-screen map rendering.
"""

import logging

from src.clients.ferry import FerryClient
from src.models.signage_data import SignageContent
from src.plugins.base_source import BaseSource
from src.plugins.registry import SourceRegistry

logger = logging.getLogger(__name__)


@SourceRegistry.register("ferry_map")
class FerryMapSource(BaseSource):
    """Ferry map data source plugin - full-screen vessel positions."""

    def validate_config(self) -> bool:
        """Validate ferry map config."""
        # No additional config needed
        return True

    def fetch_data(self) -> SignageContent | None:
        """Fetch ferry map data."""
        logger.info(f"[{self.source_id}] Fetching ferry map data")

        try:
            ferry_client = FerryClient()
            ferry_map_data = ferry_client.get_all_vessel_locations()

            if not ferry_map_data or not ferry_map_data.vessels:
                logger.warning(f"[{self.source_id}] No ferry vessel data available for map")
                return None

            logger.info(f"[{self.source_id}] Ferry map: {len(ferry_map_data.vessels)} vessels")

            # Convert to signage content
            # Note: Uses FerryMapRenderer instead of standard SignageRenderer
            return SignageContent(
                lines=[f"{len(ferry_map_data.vessels)} vessels tracked"],
                filename_prefix="ferry_map",
                layout_type="full_map",
                background_mode="ferry_map",
                background_query=None,
                metadata={"vessels": ferry_map_data.vessels, "use_map_renderer": True},
            )

        except Exception as e:
            logger.error(f"[{self.source_id}] Failed to fetch ferry map data: {e}")
            return None
