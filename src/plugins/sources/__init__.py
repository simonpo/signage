"""
Import all source plugins to register them.
This file is imported to ensure all plugins are registered with the registry.
"""

from src.plugins.sources.ambient_weather_source import (
    AmbientSensorsSource,
    AmbientWeatherSource,
)
from src.plugins.sources.ferry_map_source import FerryMapSource
from src.plugins.sources.ferry_source import FerrySource
from src.plugins.sources.football_source import FootballSource
from src.plugins.sources.nfl_source import NFLSource
from src.plugins.sources.speedtest_source import SpeedtestSource
from src.plugins.sources.stock_source import StockSource
from src.plugins.sources.system_health_source import SystemHealthSource
from src.plugins.sources.tesla_source import TeslaSource
from src.plugins.sources.weather_source import WeatherSource

__all__ = [
    "WeatherSource",
    "TeslaSource",
    "FerrySource",
    "FerryMapSource",
    "AmbientWeatherSource",
    "AmbientSensorsSource",
    "FootballSource",
    "NFLSource",
    "SpeedtestSource",
    "StockSource",
    "SystemHealthSource",
]
