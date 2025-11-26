"""
Configuration validation using Pydantic.
Validates .env configuration on startup and provides type-safe config access.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class SignageConfig(BaseSettings):
    """
    Type-safe configuration schema for the signage system.
    Automatically validates .env file on load.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore unknown env vars
    )

    # ===== Required Configuration =====

    # Home Assistant
    HA_URL: HttpUrl = Field(..., description="Home Assistant URL")
    HA_TOKEN: str = Field(..., min_length=20, description="Home Assistant long-lived access token")

    # Tesla entities (from Home Assistant)
    TESLA_BATTERY: str = Field(..., description="Tesla battery sensor entity ID")
    TESLA_RANGE: str = Field(..., description="Tesla range sensor entity ID")

    # Weather (OpenWeatherMap)
    WEATHER_CITY: str = Field(..., min_length=2, description="City name for weather")
    WEATHER_API_KEY: str = Field(..., min_length=10, description="OpenWeatherMap API key")
    WEATHER_BG_MODE: str = Field(default="local", pattern="^(local|gradient|unsplash|pexels)$")

    # ===== Optional Configuration =====

    # Ambient Weather
    AMBIENT_API_KEY: Optional[str] = Field(default=None, description="Ambient Weather API key")
    AMBIENT_APP_KEY: Optional[str] = Field(
        default=None, description="Ambient Weather application key"
    )
    AMBIENT_BG_MODE: str = Field(default="local", pattern="^(local|gradient|unsplash|pexels)$")
    AMBIENT_SENSOR_NAMES: str = Field(
        default="{}", description="JSON mapping of sensor channels to names"
    )

    # Speedtest
    SPEEDTEST_URL: Optional[str] = Field(default="http://192.168.1.36:8765")
    SPEEDTEST_TOKEN: Optional[str] = Field(default=None)
    SPEEDTEST_BG_MODE: str = Field(default="local", pattern="^(local|gradient|unsplash|pexels)$")

    # Stock Quotes
    STOCK_SYMBOL: Optional[str] = Field(default=None, description="Stock ticker symbol")
    STOCK_API_KEY: Optional[str] = Field(default=None, description="Alpha Vantage API key")
    STOCK_BG_MODE: str = Field(default="gradient", pattern="^(local|gradient|unsplash|pexels)$")

    # Ferry
    FERRY_ROUTE: Optional[str] = Field(default=None, description="Ferry route name")
    FERRY_HOME_TERMINAL: Optional[str] = Field(default=None, description="Home terminal name")
    FERRY_BG_MODE: str = Field(default="local", pattern="^(local|gradient|unsplash|pexels)$")
    WSDOT_API_KEY: Optional[str] = Field(default=None, description="WSDOT API key")

    # Marine Traffic
    MARINE_TRAFFIC_URL: Optional[str] = Field(default=None)
    MARINE_TRAFFIC_USERNAME: Optional[str] = Field(default=None)
    MARINE_TRAFFIC_PASSWORD: Optional[str] = Field(default=None)

    # Whale Tracker
    WHALE_TRACKER_URL: str = Field(default="https://whalemuseum.org/whale-sightings")

    # Sports Teams
    SEAHAWKS_ENABLED: bool = Field(default=False)
    SEAHAWKS_TEAM_ID: str = Field(default="26")
    ARSENAL_ENABLED: bool = Field(default=False)
    ARSENAL_TEAM_ID: str = Field(default="57")
    ENGLAND_RUGBY_ENABLED: bool = Field(default=False)
    BATH_RUGBY_ENABLED: bool = Field(default=False)
    ENGLAND_CRICKET_ENABLED: bool = Field(default=False)

    # API Keys
    SPORTS_API_KEY: Optional[str] = Field(default=None)
    FOOTBALL_API_KEY: Optional[str] = Field(default=None, description="football-data.org API key")
    UNSPLASH_API_KEY: Optional[str] = Field(default=None)
    PEXELS_API_KEY: Optional[str] = Field(default=None)
    GOOGLE_MAPS_API_KEY: Optional[str] = Field(default=None)

    # ===== System Configuration =====

    OUTPUT_DIR: str = Field(default="art_folder")
    FONT_PATH: str = Field(default="/System/Library/Fonts/Supplemental/Arial Bold.ttf")
    TIMEZONE: str = Field(default="US/Pacific")
    KEEP_DAYS: int = Field(default=7, ge=1, le=365)
    ENABLE_DAEMON_MODE: bool = Field(default=False)
    LIVE_UPDATE_INTERVAL: int = Field(default=120, ge=30)

    # Logging
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    LOG_FILE: Optional[str] = Field(default=None)

    # Output management
    OUTPUT_PROFILES: str = Field(default="")
    ARCHIVE_KEEP_COUNT: int = Field(default=5, ge=1)

    @field_validator("AMBIENT_SENSOR_NAMES")
    @classmethod
    def validate_sensor_names_json(cls, v: str) -> str:
        """Validate that sensor names is valid JSON."""
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"AMBIENT_SENSOR_NAMES must be valid JSON: {e}")

    @field_validator("FONT_PATH")
    @classmethod
    def validate_font_exists(cls, v: str) -> str:
        """Warn if font file doesn't exist."""
        if not Path(v).exists():
            logger.warning(f"Font file not found: {v}")
        return v

    def validate_feature_requirements(self) -> None:
        """
        Validate that enabled features have required API keys.
        Raises ValueError if configuration is incomplete.
        """
        errors = []

        # Check Arsenal requirements
        if self.ARSENAL_ENABLED and not self.FOOTBALL_API_KEY:
            errors.append("Arsenal enabled but FOOTBALL_API_KEY not set")

        # Check stock requirements
        if self.STOCK_SYMBOL and not self.STOCK_API_KEY:
            errors.append("STOCK_SYMBOL set but STOCK_API_KEY not set")

        # Check ferry requirements
        if self.FERRY_ROUTE and not self.WSDOT_API_KEY:
            errors.append("FERRY_ROUTE set but WSDOT_API_KEY not set")

        # Check ambient weather requirements
        if self.AMBIENT_API_KEY and not self.AMBIENT_APP_KEY:
            errors.append("AMBIENT_API_KEY set but AMBIENT_APP_KEY not set")
        elif self.AMBIENT_APP_KEY and not self.AMBIENT_API_KEY:
            errors.append("AMBIENT_APP_KEY set but AMBIENT_API_KEY not set")

        # Check background requirements
        for mode_var in [
            "WEATHER_BG_MODE",
            "STOCK_BG_MODE",
            "FERRY_BG_MODE",
            "AMBIENT_BG_MODE",
            "SPEEDTEST_BG_MODE",
        ]:
            mode = getattr(self, mode_var)
            if mode == "unsplash" and not self.UNSPLASH_API_KEY:
                errors.append(f"{mode_var}=unsplash but UNSPLASH_API_KEY not set")
            elif mode == "pexels" and not self.PEXELS_API_KEY:
                errors.append(f"{mode_var}=pexels but PEXELS_API_KEY not set")

        if errors:
            error_msg = "\n  - ".join(["Configuration errors:"] + errors)
            raise ValueError(error_msg)

    def create_directories(self) -> None:
        """Create required directories if they don't exist."""
        base_dir = Path(__file__).parent.parent
        output_path = base_dir / self.OUTPUT_DIR
        cache_path = base_dir / ".cache"

        for directory in [output_path, cache_path]:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")


def load_and_validate_config() -> SignageConfig:
    """
    Load and validate configuration from .env file.

    Returns:
        Validated SignageConfig instance

    Raises:
        ValidationError: If configuration is invalid
        ValueError: If feature requirements are not met
    """
    try:
        config = SignageConfig()

        logger.info("Configuration loaded successfully")
        logger.debug(f"  HA URL: {config.HA_URL}")
        logger.debug(f"  Weather: {config.WEATHER_CITY}")
        logger.debug(f"  Timezone: {config.TIMEZONE}")
        logger.debug(f"  Output: {config.OUTPUT_DIR}")

        # Validate feature requirements
        config.validate_feature_requirements()

        # Create directories
        config.create_directories()

        logger.info("✓ Configuration validation complete")

        return config

    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        logger.error("Please check your .env file")
        raise


if __name__ == "__main__":
    """Test configuration loading."""
    import sys

    logging.basicConfig(level=logging.DEBUG)

    try:
        config = load_and_validate_config()
        print("✓ Configuration is valid")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Configuration is invalid: {e}")
        sys.exit(1)
