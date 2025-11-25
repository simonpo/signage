"""
Configuration management for the signage system.
Loads all settings from .env and provides validation.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Central configuration for the signage system."""
    
    # ===== Display Settings =====
    IMAGE_WIDTH = 3840
    IMAGE_HEIGHT = 2160
    SAFE_MARGIN_H = 192  # 5% horizontal margin
    SAFE_MARGIN_V = 108  # 5% vertical margin
    
    # ===== Paths =====
    BASE_DIR = Path(__file__).parent.parent.resolve()
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "art_folder")
    OUTPUT_PATH = BASE_DIR / OUTPUT_DIR
    BACKGROUNDS_PATH = BASE_DIR / "backgrounds"
    CACHE_PATH = BASE_DIR / ".cache"
    FONT_PATH = os.getenv(
        "FONT_PATH",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    )
    
    # ===== Home Assistant =====
    HA_URL = os.getenv("HA_URL")
    HA_TOKEN = os.getenv("HA_TOKEN")
    TESLA_BATTERY = os.getenv("TESLA_BATTERY")
    TESLA_RANGE = os.getenv("TESLA_RANGE")
    
    # ===== Weather =====
    WEATHER_CITY = os.getenv("WEATHER_CITY")
    WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
    WEATHER_BG_MODE = os.getenv("WEATHER_BG_MODE", "local")
    
    # ===== Ambient Weather (Personal Weather Station) =====
    AMBIENT_API_KEY = os.getenv("AMBIENT_API_KEY")
    AMBIENT_APP_KEY = os.getenv("AMBIENT_APP_KEY")
    AMBIENT_BG_MODE = os.getenv("AMBIENT_BG_MODE", "local")
    # Sensor name mapping: JSON format {"1": "Chickens", "2": "Greenhouse"}
    AMBIENT_SENSOR_NAMES = os.getenv("AMBIENT_SENSOR_NAMES", "{}")
    
    # ===== Speedtest Tracker =====
    SPEEDTEST_URL = os.getenv("SPEEDTEST_URL", "http://192.168.1.36:8765")
    SPEEDTEST_TOKEN = os.getenv("SPEEDTEST_TOKEN", "")
    
    # ===== Stock =====
    STOCK_SYMBOL = os.getenv("STOCK_SYMBOL")
    STOCK_API_KEY = os.getenv("STOCK_API_KEY")
    STOCK_BG_MODE = os.getenv("STOCK_BG_MODE", "gradient")
    
    # ===== Ferry =====
    FERRY_ROUTE = os.getenv("FERRY_ROUTE")
    FERRY_HOME_TERMINAL = os.getenv("FERRY_HOME_TERMINAL")
    FERRY_BG_MODE = os.getenv("FERRY_BG_MODE", "local")
    WSDOT_API_KEY = os.getenv("WSDOT_API_KEY")
    
    # ===== Marine Traffic =====
    MARINE_TRAFFIC_URL = os.getenv("MARINE_TRAFFIC_URL")
    MARINE_TRAFFIC_USERNAME = os.getenv("MARINE_TRAFFIC_USERNAME")
    MARINE_TRAFFIC_PASSWORD = os.getenv("MARINE_TRAFFIC_PASSWORD")
    
    # ===== Whale Tracker =====
    WHALE_TRACKER_URL = os.getenv(
        "WHALE_TRACKER_URL",
        "https://whalemuseum.org/whale-sightings"
    )
    
    # ===== Sports =====
    ARSENAL_ENABLED = os.getenv("ARSENAL_ENABLED", "false").lower() == "true"
    SEAHAWKS_ENABLED = os.getenv("SEAHAWKS_ENABLED", "false").lower() == "true"
    ENGLAND_RUGBY_ENABLED = os.getenv("ENGLAND_RUGBY_ENABLED", "false").lower() == "true"
    BATH_RUGBY_ENABLED = os.getenv("BATH_RUGBY_ENABLED", "false").lower() == "true"
    ENGLAND_CRICKET_ENABLED = os.getenv("ENGLAND_CRICKET_ENABLED", "false").lower() == "true"
    
    SEAHAWKS_TEAM_ID = os.getenv("SEAHAWKS_TEAM_ID", "26")  # Seattle Seahawks
    ARSENAL_TEAM_ID = os.getenv("ARSENAL_TEAM_ID", "57")    # Arsenal FC
    
    # ===== API Keys =====
    SPORTS_API_KEY = os.getenv("SPORTS_API_KEY")
    FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
    UNSPLASH_API_KEY = os.getenv("UNSPLASH_API_KEY")
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
    
    # ===== Time & Scheduling =====
    TIMEZONE = os.getenv("TIMEZONE", "US/Pacific")
    KEEP_DAYS = int(os.getenv("KEEP_DAYS", "7"))
    ENABLE_DAEMON_MODE = os.getenv("ENABLE_DAEMON_MODE", "false").lower() == "true"
    LIVE_UPDATE_INTERVAL = int(os.getenv("LIVE_UPDATE_INTERVAL", "120"))
    
    @classmethod
    def validate(cls) -> None:
        """
        Validate required configuration and create necessary directories.
        Raises RuntimeError if critical settings are missing.
        """
        # Check required vars
        required = {
            "HA_URL": cls.HA_URL,
            "HA_TOKEN": cls.HA_TOKEN,
            "TESLA_BATTERY": cls.TESLA_BATTERY,
            "TESLA_RANGE": cls.TESLA_RANGE,
            "WEATHER_CITY": cls.WEATHER_CITY,
            "WEATHER_API_KEY": cls.WEATHER_API_KEY,
        }
        
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please check your .env file."
            )
        
        # Create directories
        for directory in [cls.OUTPUT_PATH, cls.CACHE_PATH]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {directory}")
        
        # Validate image dimensions
        assert cls.IMAGE_WIDTH == 3840, "Image width must be 3840px"
        assert cls.IMAGE_HEIGHT == 2160, "Image height must be 2160px"
        assert cls.SAFE_MARGIN_H == int(cls.IMAGE_WIDTH * 0.05), "H margin must be 5%"
        assert cls.SAFE_MARGIN_V == int(cls.IMAGE_HEIGHT * 0.05), "V margin must be 5%"
        
        logger.info("Configuration validated successfully")
    
    @classmethod
    def get_timezone(cls) -> pytz.timezone:
        """
        Get the configured timezone.
        Falls back to UTC if the configured timezone is invalid.
        """
        try:
            return pytz.timezone(cls.TIMEZONE)
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning(
                f"Invalid timezone '{cls.TIMEZONE}', falling back to UTC"
            )
            return pytz.UTC
    
    @classmethod
    def get_current_time(cls) -> datetime:
        """Get the current time in the configured timezone."""
        tz = cls.get_timezone()
        return datetime.now(tz)
