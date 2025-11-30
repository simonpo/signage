"""Tests for configuration validation."""

import json
import os

import pytest
from pydantic_core import ValidationError

from src.config_validator import SignageConfig


class TestSignageConfig:
    """Test configuration validation."""

    @pytest.fixture(autouse=True)
    def isolate_env(self, monkeypatch):
        """Clear environment variables before each test."""
        # Clear all signage-related env vars
        env_keys_to_clear = [
            key
            for key in os.environ
            if key.startswith(
                (
                    "HA_",
                    "TESLA_",
                    "WEATHER_",
                    "AMBIENT_",
                    "FERRY_",
                    "STOCK_",
                    "SPEEDTEST_",
                    "PEXELS_",
                    "UNSPLASH_",
                    "LOG_",
                    "OUTPUT_",
                    "ARCHIVE_",
                    "LIVE_",
                )
            )
        ]
        for key in env_keys_to_clear:
            monkeypatch.delenv(key, raising=False)

    def test_config_requires_weather_city(self, tmp_path):
        """Test that WEATHER_CITY is required."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
WEATHER_API_KEY=test_weather_key_123
"""
        )

        with pytest.raises(ValidationError) as exc_info:
            SignageConfig(_env_file=str(env_file))

        assert "WEATHER_CITY" in str(exc_info.value)

    def test_config_requires_weather_api_key(self, tmp_path):
        """Test that WEATHER_API_KEY is required."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
WEATHER_CITY=TestCity
"""
        )

        with pytest.raises(ValidationError) as exc_info:
            SignageConfig(_env_file=str(env_file))

        assert "WEATHER_API_KEY" in str(exc_info.value)

    def test_config_validates_required_fields(self, tmp_path):
        """Test that all required fields are validated."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
WEATHER_CITY=TestCity
WEATHER_API_KEY=test_weather_key_123
"""
        )

        config = SignageConfig(_env_file=str(env_file))

        assert config.WEATHER_CITY == "TestCity"
        assert config.WEATHER_API_KEY == "test_weather_key_123"  # pragma: allowlist secret

    def test_config_optional_fields_default_none(self, tmp_path):
        """Test that optional fields default to None."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
WEATHER_CITY=TestCity
WEATHER_API_KEY=test_weather_key_123
"""
        )

        config = SignageConfig(_env_file=str(env_file))

        # Required fields should be set
        assert config.WEATHER_CITY == "TestCity"
        assert config.WEATHER_API_KEY == "test_weather_key_123"
        # Optional fields default
        assert config.AMBIENT_API_KEY is None
        assert config.STOCK_API_KEY is None
        # Config loads successfully even without all optional fields
        assert config.LOG_LEVEL == "INFO"  # default value

    def test_config_background_mode_validation(self, tmp_path):
        """Test that background mode only accepts valid values."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
WEATHER_CITY=TestCity
WEATHER_API_KEY=test_weather_key_123
WEATHER_BG_MODE=invalid_mode
"""
        )

        with pytest.raises(ValidationError) as exc_info:
            SignageConfig(_env_file=str(env_file))

        assert "WEATHER_BG_MODE" in str(exc_info.value)

    def test_config_valid_background_modes(self, tmp_path):
        """Test that all valid background modes are accepted."""
        for mode in ["local", "gradient", "unsplash", "pexels"]:
            env_file = tmp_path / f".env_{mode}"
            env_file.write_text(
                f"""
WEATHER_CITY=TestCity
WEATHER_API_KEY=test_weather_key_123
WEATHER_BG_MODE={mode}
"""
            )

            config = SignageConfig(_env_file=str(env_file))
            assert mode == config.WEATHER_BG_MODE

    def test_config_ambient_sensor_names_json_parsing(self, tmp_path):
        """Test that AMBIENT_SENSOR_NAMES parses JSON correctly."""
        env_file = tmp_path / ".env"
        sensor_mapping = {"1": "Outdoor", "2": "Greenhouse", "3": "Chicken Coop"}
        env_file.write_text(
            f"""
WEATHER_CITY=TestCity
WEATHER_API_KEY=test_weather_key_123
AMBIENT_SENSOR_NAMES={json.dumps(sensor_mapping)}
"""
        )

        config = SignageConfig(_env_file=str(env_file))
        # The validator should parse this as a dict
        assert isinstance(config.AMBIENT_SENSOR_NAMES, str)
        parsed = json.loads(config.AMBIENT_SENSOR_NAMES)
        assert parsed == sensor_mapping

    def test_config_ignores_extra_env_vars(self, tmp_path):
        """Test that extra environment variables are ignored."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
WEATHER_CITY=TestCity
WEATHER_API_KEY=test_weather_key_123
UNKNOWN_VAR=should_be_ignored
ANOTHER_UNKNOWN=also_ignored
"""
        )

        # Should not raise an error
        config = SignageConfig(_env_file=str(env_file))
        assert config.WEATHER_CITY == "TestCity"

    def test_config_log_level_validation(self, tmp_path):
        """Test that LOG_LEVEL only accepts valid values."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            """
WEATHER_CITY=TestCity
WEATHER_API_KEY=test_weather_key_123
LOG_LEVEL=INVALID
"""
        )

        with pytest.raises(ValidationError) as exc_info:
            SignageConfig(_env_file=str(env_file))

        assert "LOG_LEVEL" in str(exc_info.value)

    def test_config_valid_log_levels(self, tmp_path):
        """Test that all valid log levels are accepted."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            env_file = tmp_path / f".env_{level}"
            env_file.write_text(
                f"""
WEATHER_CITY=TestCity
WEATHER_API_KEY=test_weather_key_123
LOG_LEVEL={level}
"""
            )

            config = SignageConfig(_env_file=str(env_file))
            assert level == config.LOG_LEVEL
