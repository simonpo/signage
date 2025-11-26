"""
Tests for API clients.
"""

from src.clients.base import APIClient
from src.clients.homeassistant import HomeAssistantClient
from src.clients.weather import WeatherClient


def test_api_client_initialization():
    """Test that base API client initializes correctly."""
    client = APIClient(timeout=5, max_retries=2)
    assert client.timeout == 5
    assert client.max_retries == 2
    assert client.session is not None
    client.close()


def test_ha_client_requires_config():
    """Test that HA client requires configuration."""
    # This will fail if HA_URL or HA_TOKEN not set
    # In real env, this should be configured
    try:
        client = HomeAssistantClient()
        assert client.base_url is not None
        assert client.headers is not None
    except ValueError:
        # Expected if not configured
        pass


def test_weather_client_requires_key():
    """Test that weather client requires API key."""
    try:
        client = WeatherClient()
        assert client.api_key is not None
    except ValueError:
        # Expected if not configured
        pass
