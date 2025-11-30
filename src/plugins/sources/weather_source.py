"""
Weather data source plugin.
Wraps WeatherClient from existing codebase.
"""

import logging

from src.clients.weather import WeatherClient
from src.models.signage_data import SignageContent
from src.plugins.base_source import BaseSource
from src.plugins.registry import SourceRegistry

logger = logging.getLogger(__name__)


@SourceRegistry.register("weather")
class WeatherSource(BaseSource):
    """Weather data source plugin."""

    def validate_config(self) -> bool:
        """Validate weather config."""
        if "city" not in self.config:
            raise ValueError("Weather source requires 'city' in config")

        if "api_key" not in self.config:
            raise ValueError("Weather source requires 'api_key' in config")

        return True

    def fetch_data(self) -> SignageContent | None:
        """Fetch weather data."""
        city = self.config["city"]
        api_key = self.config["api_key"]

        logger.info(f"[{self.source_id}] Fetching weather for {city}")

        # Create client with temporary config override
        # Note: WeatherClient currently uses Config, we'll need to adapt it
        # For now, use existing get_weather() and adapt city
        from src.config import Config

        # Temporarily override config (this is a workaround until we refactor WeatherClient)
        original_city = Config.WEATHER_CITY
        original_key = Config.WEATHER_API_KEY

        try:
            Config.WEATHER_CITY = city
            Config.WEATHER_API_KEY = api_key

            client = WeatherClient()
            weather_data = client.get_weather()

            if not weather_data:
                logger.warning(f"[{self.source_id}] No weather data for {city}")
                return None

            # Convert to signage content
            return weather_data.to_signage()

        finally:
            # Restore original config
            Config.WEATHER_CITY = original_city
            Config.WEATHER_API_KEY = original_key
