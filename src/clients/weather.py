"""
Weather API client using OpenWeatherMap.
Maps weather conditions to background categories.
"""

import logging
from typing import Optional

from src.clients.base import APIClient
from src.config import Config
from src.models.signage_data import WeatherData

logger = logging.getLogger(__name__)


class WeatherClient(APIClient):
    """Client for OpenWeatherMap API."""

    BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

    # Map OWM conditions to our background categories
    CONDITION_MAP = {
        "Clear": "sunny",
        "Clouds": "cloudy",
        "Rain": "rainy",
        "Drizzle": "rainy",
        "Thunderstorm": "thunderstorm",
        "Snow": "snowy",
        "Mist": "foggy",
        "Fog": "foggy",
        "Haze": "foggy",
        "Smoke": "foggy",
        "Dust": "cloudy",
        "Sand": "cloudy",
        "Ash": "cloudy",
        "Squall": "windy",
        "Tornado": "windy",
    }

    def __init__(self):
        """Initialize with API key from config."""
        super().__init__()

        if not Config.WEATHER_API_KEY:
            raise ValueError("WEATHER_API_KEY must be configured")

        self.api_key = Config.WEATHER_API_KEY
        self.city = Config.WEATHER_CITY

    def get_weather(self) -> Optional[WeatherData]:
        """
        Fetch current weather for configured city.

        Returns:
            WeatherData object or None on failure
        """
        params = {"q": self.city, "appid": self.api_key, "units": "imperial"}  # Fahrenheit

        response = self._make_request(self.BASE_URL, params=params)

        if not response:
            logger.error("Failed to fetch weather data")
            return None

        try:
            data = response.json()

            # Main weather data
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            temp_high = data["main"]["temp_max"]
            temp_low = data["main"]["temp_min"]
            humidity = data["main"]["humidity"]

            # Weather condition
            description = data["weather"][0]["description"].title()
            main_condition = data["weather"][0]["main"]

            # Wind data
            wind_speed = data.get("wind", {}).get("speed", 0)
            wind_direction = data.get("wind", {}).get("deg", 0)

            # Visibility (in meters)
            visibility = data.get("visibility")

            # Map to our background categories
            condition = self.CONDITION_MAP.get(main_condition, "default")

            weather = WeatherData(
                city=self.city,
                temperature=temp,
                description=description,
                condition=condition,
                feels_like=feels_like,
                temp_high=temp_high,
                temp_low=temp_low,
                humidity=humidity,
                wind_speed=wind_speed,
                wind_direction=wind_direction,
                visibility=visibility,
            )

            logger.info(f"Weather: {temp}°F, {description}, Humidity: {humidity}%")
            return weather

        except (ValueError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse weather response: {e}")
            return None
