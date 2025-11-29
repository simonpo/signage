"""Tests for Tesla vehicle data caching."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.clients.tesla_fleet import TeslaFleetClient


@pytest.fixture
def mock_tesla_config():
    """Mock Tesla configuration."""
    with patch("src.clients.tesla_fleet.Config") as mock_config:
        mock_config.TESLA_CLIENT_ID = "test_client_id"
        mock_config.TESLA_CLIENT_SECRET = "test_client_secret"  # pragma: allowlist secret
        mock_config.TESLA_REGION = "na"
        yield mock_config


@pytest.fixture
def mock_cache_file():
    """Create a temporary cache file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        cache_data = {
            "test_vehicle_123": {
                "data": {
                    "charge_state": {"battery_level": 75, "battery_range": 220.0},
                    "vehicle_state": {"odometer": 15000.0, "locked": True},
                },
                "cached_at": "2025-11-28T10:00:00.000000",
            }
        }
        json.dump(cache_data, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)


def test_cache_vehicle_data(tmp_path, mock_tesla_config):
    """Test caching vehicle data to file."""
    cache_file = tmp_path / "test_cache.json"

    # Monkey-patch the cache file location
    original_cache = TeslaFleetClient.VEHICLE_CACHE_FILE
    TeslaFleetClient.VEHICLE_CACHE_FILE = cache_file

    try:
        # This will fail auth but we just need to test caching
        client = TeslaFleetClient()

        # Test data
        vehicle_id = "test_vehicle_456"
        test_data = {
            "charge_state": {"battery_level": 80},
            "vehicle_state": {"odometer": 19000.0},
        }

        # Cache the data
        client._cache_vehicle_data(vehicle_id, test_data)

        # Verify file was created
        assert cache_file.exists()

        # Verify cached data
        with open(cache_file) as f:
            cached = json.load(f)

        assert vehicle_id in cached
        assert cached[vehicle_id]["data"] == test_data
        assert "cached_at" in cached[vehicle_id]

    finally:
        TeslaFleetClient.VEHICLE_CACHE_FILE = original_cache


def test_get_cached_vehicle_data(mock_cache_file, mock_tesla_config):
    """Test retrieving cached vehicle data."""
    # Monkey-patch the cache file location
    original_cache = TeslaFleetClient.VEHICLE_CACHE_FILE
    TeslaFleetClient.VEHICLE_CACHE_FILE = mock_cache_file

    try:
        client = TeslaFleetClient()

        # Retrieve cached data
        cached = client.get_cached_vehicle_data("test_vehicle_123")

        assert cached is not None
        assert "data" in cached
        assert "cached_at" in cached
        assert cached["data"]["charge_state"]["battery_level"] == 75

    finally:
        TeslaFleetClient.VEHICLE_CACHE_FILE = original_cache


def test_get_cached_vehicle_data_missing(mock_tesla_config):
    """Test retrieving cached data for non-existent vehicle."""
    # Use non-existent cache file
    original_cache = TeslaFleetClient.VEHICLE_CACHE_FILE
    TeslaFleetClient.VEHICLE_CACHE_FILE = Path("/tmp/nonexistent_cache_12345.json")

    try:
        client = TeslaFleetClient()
        cached = client.get_cached_vehicle_data("test_vehicle_999")

        assert cached is None

    finally:
        TeslaFleetClient.VEHICLE_CACHE_FILE = original_cache


def test_cache_overwrites_old_data(tmp_path, mock_tesla_config):
    """Test that caching updates existing vehicle data."""
    cache_file = tmp_path / "test_cache_overwrite.json"

    # Create initial cache
    initial_data = {
        "vehicle_123": {
            "data": {"charge_state": {"battery_level": 50}},
            "cached_at": "2025-11-28T09:00:00.000000",
        }
    }
    with open(cache_file, "w") as f:
        json.dump(initial_data, f)

    original_cache = TeslaFleetClient.VEHICLE_CACHE_FILE
    TeslaFleetClient.VEHICLE_CACHE_FILE = cache_file

    try:
        client = TeslaFleetClient()

        # Update with new data
        new_data = {"charge_state": {"battery_level": 75}}
        client._cache_vehicle_data("vehicle_123", new_data)

        # Verify update
        with open(cache_file) as f:
            cached = json.load(f)

        assert cached["vehicle_123"]["data"]["charge_state"]["battery_level"] == 75
        # Timestamp should be updated
        assert cached["vehicle_123"]["cached_at"] != "2025-11-28T09:00:00.000000"

    finally:
        TeslaFleetClient.VEHICLE_CACHE_FILE = original_cache
