"""
Tests for WeatherClient with mocked HTTP responses.
"""

import pytest
import responses

from src.clients.weather import WeatherClient
from src.config import Config


@pytest.fixture
def mock_weather_response():
    """Sample OpenWeatherMap API response."""
    return {
        "weather": [{"main": "Clear", "description": "clear sky", "icon": "01d"}],
        "main": {
            "temp": 72.5,
            "feels_like": 70.0,
            "temp_min": 68.0,
            "temp_max": 75.0,
            "pressure": 1013,
            "humidity": 65,
        },
        "visibility": 10000,
        "wind": {"speed": 8.5, "deg": 180, "gust": 12.0},
        "clouds": {"all": 20},
        "dt": 1701187200,
        "sys": {"sunrise": 1701166800, "sunset": 1701201600},
        "name": "Seattle",
    }


@pytest.fixture
def mock_rainy_response():
    """Sample rainy weather response."""
    return {
        "weather": [{"main": "Rain", "description": "light rain", "icon": "10d"}],
        "main": {
            "temp": 55.0,
            "feels_like": 52.0,
            "temp_min": 50.0,
            "temp_max": 58.0,
            "pressure": 1008,
            "humidity": 85,
        },
        "visibility": 5000,
        "wind": {"speed": 12.0, "deg": 200},
        "clouds": {"all": 90},
        "rain": {"1h": 2.5},
        "dt": 1701187200,
        "sys": {"sunrise": 1701166800, "sunset": 1701201600},
        "name": "Seattle",
    }


class TestWeatherClient:
    """Test WeatherClient with mocked API responses."""

    @responses.activate
    def test_get_weather_success(self, mock_weather_response, monkeypatch):
        """Test successful weather fetch."""
        monkeypatch.setattr(Config, "WEATHER_API_KEY", "test_key_123")
        monkeypatch.setattr(Config, "WEATHER_CITY", "Seattle,US")

        # Mock the API response
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/weather",
            json=mock_weather_response,
            status=200,
        )

        client = WeatherClient()
        weather = client.get_weather()

        assert weather is not None
        assert weather.city == "Seattle,US"  # Uses full city query
        assert weather.temperature == 72.5
        assert weather.feels_like == 70.0
        assert weather.temp_high == 75.0
        assert weather.temp_low == 68.0
        assert weather.condition == "sunny"  # Clear -> sunny
        assert weather.humidity == 65
        assert weather.wind_speed == 8.5

    @responses.activate
    def test_get_weather_rainy_condition(self, mock_rainy_response, monkeypatch):
        """Test weather with rainy condition mapping."""
        monkeypatch.setattr(Config, "WEATHER_API_KEY", "test_key_123")
        monkeypatch.setattr(Config, "WEATHER_CITY", "Seattle,US")

        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/weather",
            json=mock_rainy_response,
            status=200,
        )

        client = WeatherClient()
        weather = client.get_weather()

        assert weather is not None
        assert weather.condition == "rainy"  # Rain -> rainy
        assert weather.rain_1h == 2.5
        assert weather.humidity == 85

    @responses.activate
    def test_get_weather_api_error(self, monkeypatch):
        """Test handling of API error response."""
        monkeypatch.setattr(Config, "WEATHER_API_KEY", "test_key_123")
        monkeypatch.setattr(Config, "WEATHER_CITY", "Seattle,US")

        # Mock 404 error
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/weather",
            json={"cod": "404", "message": "city not found"},
            status=404,
        )

        client = WeatherClient()
        weather = client.get_weather()

        assert weather is None

    @responses.activate
    def test_get_weather_invalid_json(self, monkeypatch):
        """Test handling of malformed JSON response."""
        monkeypatch.setattr(Config, "WEATHER_API_KEY", "test_key_123")
        monkeypatch.setattr(Config, "WEATHER_CITY", "Seattle,US")

        # Mock malformed response
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/weather",
            body="Invalid JSON",
            status=200,
        )

        client = WeatherClient()
        weather = client.get_weather()

        assert weather is None

    @responses.activate
    def test_get_weather_missing_fields(self, monkeypatch):
        """Test handling of response with missing fields."""
        monkeypatch.setattr(Config, "WEATHER_API_KEY", "test_key_123")
        monkeypatch.setattr(Config, "WEATHER_CITY", "Seattle,US")

        # Mock incomplete response
        responses.add(
            responses.GET,
            "http://api.openweathermap.org/data/2.5/weather",
            json={"name": "Seattle"},  # Missing most fields
            status=200,
        )

        client = WeatherClient()
        weather = client.get_weather()

        assert weather is None

    def test_weather_client_requires_api_key(self, monkeypatch):
        """Test that WeatherClient requires API key."""
        monkeypatch.setattr(Config, "WEATHER_API_KEY", None)
        monkeypatch.setattr(Config, "WEATHER_CITY", "Seattle,US")

        with pytest.raises(ValueError, match="WEATHER_API_KEY must be configured"):
            WeatherClient()

    @responses.activate
    def test_weather_condition_mapping(self, monkeypatch):
        """Test various weather condition mappings."""
        monkeypatch.setattr(Config, "WEATHER_API_KEY", "test_key_123")
        monkeypatch.setattr(Config, "WEATHER_CITY", "Seattle,US")

        test_cases = [
            ("Clear", "sunny"),
            ("Clouds", "cloudy"),
            ("Rain", "rainy"),
            ("Drizzle", "rainy"),
            ("Thunderstorm", "thunderstorm"),
            ("Snow", "snowy"),
            ("Fog", "foggy"),
            ("Mist", "foggy"),
        ]

        for owm_condition, expected_condition in test_cases:
            responses.reset()
            responses.add(
                responses.GET,
                "http://api.openweathermap.org/data/2.5/weather",
                json={
                    "weather": [{"main": owm_condition, "description": "test"}],
                    "main": {
                        "temp": 70.0,
                        "feels_like": 68.0,
                        "temp_min": 65.0,
                        "temp_max": 75.0,
                        "pressure": 1013,
                        "humidity": 60,
                    },
                    "wind": {"speed": 5.0, "deg": 180},
                    "name": "Seattle",
                },
                status=200,
            )

            client = WeatherClient()
            weather = client.get_weather()

            assert weather is not None
            assert (
                weather.condition == expected_condition
            ), f"Expected {owm_condition} -> {expected_condition}"
