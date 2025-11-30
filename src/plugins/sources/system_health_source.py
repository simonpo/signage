"""
System health data source plugin.
Wraps SystemHealthClient from existing codebase.
"""

import logging
from datetime import datetime

from src.clients.system_health import SystemHealthClient
from src.models.signage_data import SignageContent, SystemHealthData
from src.plugins.base_source import BaseSource
from src.plugins.registry import SourceRegistry

logger = logging.getLogger(__name__)


@SourceRegistry.register("system_health")
class SystemHealthSource(BaseSource):
    """System health monitoring data source plugin."""

    def validate_config(self) -> bool:
        """Validate system health config."""
        # No additional config needed
        return True

    def fetch_data(self) -> SignageContent | None:
        """Fetch system health data."""
        logger.info(f"[{self.source_id}] Fetching system health data")

        try:
            health_client = SystemHealthClient()
            health_data = health_client.get_health_data()

            if not health_data:
                logger.warning(f"[{self.source_id}] No system health data available")
                return None

            # Calculate status
            generators = health_data.get("generators", {})
            total_failures = sum(g.get("failure", 0) for g in generators.values())
            total_runs = sum(g.get("success", 0) + g.get("failure", 0) for g in generators.values())
            success_rate = (
                (total_runs - total_failures) / total_runs * 100 if total_runs > 0 else 100
            )

            if success_rate >= 95:
                status = "HEALTHY"
            elif success_rate >= 80:
                status = "DEGRADED"
            else:
                status = "DOWN"

            # Format time_ago for each generator
            now = datetime.now()
            for _name, stats in generators.items():
                if stats.get("last_run"):
                    delta = now - stats["last_run"]
                    if delta.total_seconds() < 60:
                        stats["time_ago"] = f"{int(delta.total_seconds())}s ago"
                    elif delta.total_seconds() < 3600:
                        stats["time_ago"] = f"{int(delta.total_seconds() / 60)}m ago"
                    else:
                        stats["time_ago"] = f"{int(delta.total_seconds() / 3600)}h ago"
                else:
                    stats["time_ago"] = "never"

            # Create data model
            system_data = SystemHealthData(
                status=status,
                uptime=health_data["uptime"]["formatted"],
                generators=generators,
                recent_errors=health_data.get("recent_errors", []),
                disk_space=health_data.get("disk_space", {}),
                images_generated=health_data.get("images_generated", {}),
                log_file_size=health_data.get("log_file_size", {}),
            )

            logger.info(f"[{self.source_id}] System status: {status}")

            # Convert to signage content
            return system_data.to_signage()

        except Exception as e:
            logger.error(f"[{self.source_id}] Failed to fetch system health data: {e}")
            return None
