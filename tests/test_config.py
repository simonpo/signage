"""
Tests for configuration module.
"""


import pytest

from src.config import Config


def test_image_dimensions():
    """Test that image dimensions are correct for 4K."""
    assert Config.IMAGE_WIDTH == 3840
    assert Config.IMAGE_HEIGHT == 2160


def test_safe_margins():
    """Test that safe margins are 5% of dimensions."""
    assert Config.SAFE_MARGIN_H == 192  # 5% of 3840
    assert Config.SAFE_MARGIN_V == 108  # 5% of 2160


def test_timezone_handling():
    """Test timezone configuration."""
    tz = Config.get_timezone()
    assert tz is not None

    # Test current time retrieval
    now = Config.get_current_time()
    assert now is not None


def test_validation_missing_required():
    """Test that validation fails with missing required vars."""
    # Skip this test - Config.validate() is deprecated in favor of config_validator
    # The new pydantic-based validator is tested separately
    pytest.skip("Config.validate() deprecated - using pydantic validator instead")
