"""
System health client for collecting system metrics.
"""

import logging
from typing import Any

from src.clients.base import APIClient
from src.utils.system_stats import SystemStats

logger = logging.getLogger(__name__)


class SystemHealthClient(APIClient):
    """Client for collecting system health metrics."""

    def __init__(self):
        """Initialize system health client."""
        super().__init__()
        self.stats = SystemStats()

    def get_health_data(self) -> dict[str, Any] | None:
        """
        Collect system health statistics.

        Returns:
            Dictionary with system health metrics or None on failure
        """
        try:
            stats = self.stats.get_stats()
            logger.info("Collected system health statistics")
            return stats
        except Exception as e:
            logger.error(f"Failed to collect system health: {e}")
            return None
