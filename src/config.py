"""
Configuration validation using Pydantic.
Validates .env configuration on startup and provides type-safe config access.

This replaces the old src/config.py class-based config system with a
type-safe Pydantic model that validates on load.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import pytz
from pydantic import Field, field_validator
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

    # ===== Display Settings =====
    IMAGE_WIDTH: int = Field(default=3840, description="Output image width")
    IMAGE_HEIGHT: int = Field(default=2160, description="Output image height")
    SAFE_MARGIN_H: int = Field(default=192, description="Horizontal safe margin (5%)")
    SAFE_MARGIN_V: int = Field(default=108, description="Vertical safe margin (5%)")

    # ===== Paths =====
    OUTPUT_DIR: str = Field(default="art_folder")
    FONT_PATH: str = Field(default="/System/Library/Fonts/Supplemental/Arial Bold.ttf")

    # ===== TV Configuration (Optional) =====
    TV_IP: str | None = Field(default=None, description="Samsung Frame TV IP address")
    TV_PORT: int = Field(default=8002, description="Samsung TV websocket port")

    # ===== Tesla Fleet API (Optional) =====
    TESLA_CLIENT_ID: str | None = Field(default=None, description="Tesla Fleet API client ID")
    TESLA_CLIENT_SECRET: str | None = Field(default=None, description="Tesla Fleet API secret")
    TESLA_REGION: str = Field(default="na", pattern="^(na|eu|cn)$", description="Tesla region")

    # ===== Required Configuration =====

    # Weather (OpenWeatherMap)
    WEATHER_CITY: str = Field(..., min_length=2, description="City name for weather")
    WEATHER_API_KEY: str = Field(..., min_length=10, description="OpenWeatherMap API key")
    WEATHER_BG_MODE: str = Field(default="local", pattern="^(local|gradient|unsplash|pexels)$")

    # ===== Optional Configuration =====

    # Ambient Weather
    AMBIENT_API_KEY: str | None = Field(default=None, description="Ambient Weather API key")
    AMBIENT_APP_KEY: str | None = Field(default=None, description="Ambient Weather application key")
    AMBIENT_BG_MODE: str = Field(default="local", pattern="^(local|gradient|unsplash|pexels)$")
    AMBIENT_SENSOR_NAMES: str = Field(
        default="{}", description="JSON mapping of sensor channels to names"
    )

    # Speedtest
    SPEEDTEST_URL: str | None = Field(default="http://192.168.1.36:8765")
    SPEEDTEST_TOKEN: str | None = Field(default=None)
    SPEEDTEST_BG_MODE: str = Field(default="local", pattern="^(local|gradient|unsplash|pexels)$")

    # Stock Quotes
    STOCK_SYMBOL: str | None = Field(default=None, description="Stock ticker symbol")
    STOCK_API_KEY: str | None = Field(default=None, description="Alpha Vantage API key")
    STOCK_BG_MODE: str = Field(default="gradient", pattern="^(local|gradient|unsplash|pexels)$")

    # Ferry
    FERRY_ROUTE: str | None = Field(default=None, description="Ferry route name")
    FERRY_HOME_TERMINAL: str | None = Field(default=None, description="Home terminal name")
    FERRY_BG_MODE: str = Field(default="local", pattern="^(local|gradient|unsplash|pexels)$")
    WSDOT_API_KEY: str | None = Field(default=None, description="WSDOT API key")

    # Sports Teams
    SEAHAWKS_ENABLED: bool = Field(default=False)
    SEAHAWKS_TEAM_ID: str = Field(default="26")
    ARSENAL_ENABLED: bool = Field(default=False)
    ARSENAL_TEAM_ID: str = Field(default="57")
    ENGLAND_RUGBY_ENABLED: bool = Field(default=False)
    BATH_RUGBY_ENABLED: bool = Field(default=False)
    ENGLAND_CRICKET_ENABLED: bool = Field(default=False)

    # API Keys
    SPORTS_API_KEY: str | None = Field(default=None)
    FOOTBALL_API_KEY: str | None = Field(default=None, description="football-data.org API key")
    UNSPLASH_API_KEY: str | None = Field(default=None)
    PEXELS_API_KEY: str | None = Field(default=None)
    GOOGLE_MAPS_API_KEY: str | None = Field(default=None)

    # ===== System Configuration =====
    TIMEZONE: str = Field(default="US/Pacific")
    KEEP_DAYS: int = Field(default=7, ge=1, le=365)
    ENABLE_DAEMON_MODE: bool = Field(default=False)
    LIVE_UPDATE_INTERVAL: int = Field(default=120, ge=30)

    # Logging
    LOG_LEVEL: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    LOG_FILE: str | None = Field(default=None)

    # Output management
    OUTPUT_PROFILES: str = Field(default="")
    ARCHIVE_KEEP_COUNT: int = Field(default=5, ge=1)

    # ===== Validators =====

    @field_validator("AMBIENT_SENSOR_NAMES")
    @classmethod
    def validate_sensor_names_json(cls, v: str) -> str:
        """Validate that sensor names is valid JSON."""
        try:
            json.loads(v)
            return v
        except json.JSONDecodeError as e:
            raise ValueError(f"AMBIENT_SENSOR_NAMES must be valid JSON: {e}") from e

    @field_validator("FONT_PATH")
    @classmethod
    def validate_font_exists(cls, v: str) -> str:
        """Warn if font file doesn't exist."""
        if not Path(v).exists():
            logger.warning(f"Font file not found: {v}")
        return v

    @field_validator("TV_IP")
    @classmethod
    def validate_tv_ip(cls, v: str | None) -> str | None:
        """Warn if TV_IP is not set (won't upload to TV)."""
        if not v:
            logger.warning("TV_IP not set - images will be generated but not uploaded to TV")
        return v

    @field_validator("IMAGE_WIDTH", "IMAGE_HEIGHT")
    @classmethod
    def validate_dimensions(cls, v: int, info) -> int:
        """Validate display dimensions."""
        if info.field_name == "IMAGE_WIDTH" and v != 3840:
            raise ValueError("IMAGE_WIDTH must be 3840px for 4K displays")
        if info.field_name == "IMAGE_HEIGHT" and v != 2160:
            raise ValueError("IMAGE_HEIGHT must be 2160px for 4K displays")
        return v

    @field_validator("SAFE_MARGIN_H")
    @classmethod
    def validate_safe_margin_h(cls, v: int) -> int:
        """Validate horizontal margin is 5% of width."""
        if v != 192:  # 5% of 3840
            raise ValueError("SAFE_MARGIN_H must be 192 (5% of 3840)")
        return v

    @field_validator("SAFE_MARGIN_V")
    @classmethod
    def validate_safe_margin_v(cls, v: int) -> int:
        """Validate vertical margin is 5% of height."""
        if v != 108:  # 5% of 2160
            raise ValueError("SAFE_MARGIN_V must be 108 (5% of 2160)")
        return v

    # ===== Properties for backward compatibility =====

    @property
    def BASE_DIR(self) -> Path:  # noqa: N802
        """Get base directory of the project."""
        return Path(__file__).parent.parent.resolve()

    @property
    def OUTPUT_PATH(self) -> Path:  # noqa: N802
        """Get output directory path."""
        return self.BASE_DIR / self.OUTPUT_DIR

    @property
    def BACKGROUNDS_PATH(self) -> Path:  # noqa: N802
        """Get backgrounds directory path."""
        return self.BASE_DIR / "backgrounds"

    @property
    def CACHE_PATH(self) -> Path:  # noqa: N802
        """Get cache directory path."""
        return self.BASE_DIR / ".cache"

    # ===== Helper Methods =====

    def get_timezone(self) -> pytz.BaseTzInfo:
        """
        Get the configured timezone.
        Falls back to UTC if the configured timezone is invalid.
        """
        try:
            return pytz.timezone(self.TIMEZONE)
        except pytz.exceptions.UnknownTimeZoneError:
            logger.warning(f"Invalid timezone '{self.TIMEZONE}', falling back to UTC")
            return pytz.UTC

    def get_current_time(self) -> datetime:
        """Get the current time in the configured timezone."""
        tz = self.get_timezone()
        return datetime.now(tz)

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
        for directory in [self.OUTPUT_PATH, self.CACHE_PATH]:
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


# ===== Singleton Instance =====
# This replaces the old Config class with a validated instance
# Import this as: from src.config import Config
try:
    Config = load_and_validate_config()
except Exception as e:
    # Allow import even if config is invalid (for testing, docs generation, etc.)
    logger.warning(f"Failed to load config: {e}")
    Config = None  # type: ignore


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
