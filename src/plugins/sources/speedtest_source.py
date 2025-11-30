"""
Speedtest data source plugin.
Wraps SpeedtestClient from existing codebase.
"""

import logging

from src.clients.speedtest import SpeedtestClient
from src.models.signage_data import SignageContent
from src.plugins.base_source import BaseSource
from src.plugins.registry import SourceRegistry

logger = logging.getLogger(__name__)


@SourceRegistry.register("speedtest")
class SpeedtestSource(BaseSource):
    """Internet speedtest data source plugin."""

    def validate_config(self) -> bool:
        """Validate speedtest config."""
        # No additional config needed - uses Config for URL and token
        return True

    def fetch_data(self) -> SignageContent | None:
        """Fetch speedtest data."""
        logger.info(f"[{self.source_id}] Fetching speedtest data")

        try:
            client = SpeedtestClient()
            speedtest_data = client.get_latest()

            if not speedtest_data:
                logger.warning(f"[{self.source_id}] No speedtest data available")
                return None

            logger.info(
                f"[{self.source_id}] {speedtest_data.download:.0f}↓ "
                f"{speedtest_data.upload:.0f}↑ Mbps"
            )

            # Convert to signage content
            return speedtest_data.to_signage()

        except Exception as e:
            logger.error(f"[{self.source_id}] Failed to fetch speedtest data: {e}")
            return None
