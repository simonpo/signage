"""
Ferry data source plugin.
Wraps FerryClient from existing codebase.
"""

import logging

from src.clients.ferry import FerryClient
from src.models.signage_data import SignageContent
from src.plugins.base_source import BaseSource
from src.plugins.registry import SourceRegistry

logger = logging.getLogger(__name__)


@SourceRegistry.register("ferry")
class FerrySource(BaseSource):
    """Ferry schedule data source plugin."""

    def validate_config(self) -> bool:
        """Validate ferry config."""
        # For now, ferry client uses Config directly
        # In future, could accept route_id and terminal_id in config
        return True

    def fetch_data(self) -> SignageContent | None:
        """Fetch ferry schedule data."""
        logger.info(f"[{self.source_id}] Fetching ferry schedule")

        try:
            client = FerryClient()
            ferry_data = client.get_ferry_data()

            if not ferry_data:
                logger.warning(f"[{self.source_id}] No ferry data available")
                return None

            # Generate map if we have vessel data
            map_path = None
            if ferry_data.vessels:

                from src.config import Config
                from src.renderers.map_renderer import MapRenderer

                map_renderer = MapRenderer()
                ferry_map = map_renderer.render_ferry_map(ferry_data.vessels)

                # Save map temporarily
                map_path = Config.CACHE_PATH / "ferry_map_temp.jpg"
                ferry_map.save(map_path, "JPEG", quality=95)

            # Convert to signage content
            return ferry_data.to_signage(map_path)

        except Exception as e:
            logger.error(f"[{self.source_id}] Failed to fetch ferry data: {e}")
            return None
