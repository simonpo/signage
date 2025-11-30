"""
Tests for API clients.
"""

from src.clients.base import APIClient
from src.clients.sports.nfl import NFLClient
from src.clients.weather import WeatherClient


def test_api_client_initialization():
    """Test that base API client initializes correctly."""
    client = APIClient(timeout=5, max_retries=2)
    assert client.timeout == 5
    assert client.max_retries == 2
    assert client.session is not None
    client.close()


def test_nfl_client_initialization():
    """Test that NFL client initializes correctly."""
    client = NFLClient()
    assert client.session is not None
    assert client.timeout == 10
    assert client.ESPN_BASE == "https://site.api.espn.com/apis/site/v2/sports/football/nfl"
    client.close()


def test_weather_client_requires_key():
    """Test that weather client requires API key."""
    try:
        client = WeatherClient()
        assert client.api_key is not None
    except ValueError:
        # Expected if not configured
        pass
