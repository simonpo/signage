"""
Ambient Weather data source plugin.
Wraps AmbientWeatherClient from existing codebase.
"""

import logging

from src.clients.ambient_weather import AmbientWeatherClient
from src.models.signage_data import SignageContent
from src.plugins.base_source import BaseSource
from src.plugins.registry import SourceRegistry

logger = logging.getLogger(__name__)


@SourceRegistry.register("ambient_weather")
class AmbientWeatherSource(BaseSource):
    """Ambient Weather station data source plugin."""

    def validate_config(self) -> bool:
        """Validate ambient weather config."""
        # No additional config needed - uses Config for API keys
        return True

    def fetch_data(self) -> SignageContent | None:
        """Fetch ambient weather station data."""
        logger.info(f"[{self.source_id}] Fetching ambient weather data")

        try:
            client = AmbientWeatherClient()
            ambient_data = client.get_weather()

            if not ambient_data:
                logger.warning(f"[{self.source_id}] No ambient weather data available")
                return None

            # Convert to signage content
            return ambient_data.to_signage()

        except Exception as e:
            logger.error(f"[{self.source_id}] Failed to fetch ambient weather data: {e}")
            return None


@SourceRegistry.register("ambient_sensors")
class AmbientSensorsSource(BaseSource):
    """Ambient Weather multi-sensor data source plugin."""

    def validate_config(self) -> bool:
        """Validate ambient sensors config."""
        # No additional config needed - uses Config for API keys and sensor names
        return True

    def fetch_data(self) -> SignageContent | None:
        """Fetch ambient weather sensor data."""
        logger.info(f"[{self.source_id}] Fetching ambient sensor data")

        try:
            client = AmbientWeatherClient()
            sensor_data = client.get_all_sensors()

            if not sensor_data:
                logger.warning(f"[{self.source_id}] No ambient sensor data available")
                return None

            logger.info(
                f"[{self.source_id}] Outdoor {sensor_data.outdoor_temp:.1f}°F, "
                f"{len(sensor_data.sensors)} additional sensors"
            )

            # Convert to signage content
            return sensor_data.to_signage()

        except Exception as e:
            logger.error(f"[{self.source_id}] Failed to fetch ambient sensor data: {e}")
            return None
