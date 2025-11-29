"""
Tests for SpeedtestClient with mocked HTTP responses.
"""

import pytest
import responses

from src.clients.speedtest import SpeedtestClient
from src.config import Config


@pytest.fixture
def mock_speedtest_response():
    """Sample Speedtest Tracker API response."""
    return {
        "message": "ok",
        "data": {
            "id": 12345,
            "download": 245.67,
            "upload": 89.12,
            "ping": 12.5,
            "server_name": "Example ISP",
            "server_host": "speedtest.example.com",
            "url": "http://www.speedtest.net/result/12345",
            "created_at": "2025-11-27T14:30:00.000000Z",
        },
    }


@pytest.fixture
def mock_error_response():
    """Error response from Speedtest Tracker."""
    return {"message": "error", "error": "Unauthorized"}


@pytest.fixture
def mock_missing_fields_response():
    """Response with missing required fields."""
    return {
        "message": "ok",
        "data": {
            "id": 12345,
            "download": 245.67,
            # Missing upload and ping
            "server_name": "Example ISP",
        },
    }


class TestSpeedtestClient:
    """Test SpeedtestClient with mocked API responses."""

    @responses.activate
    def test_get_latest_success(self, mock_speedtest_response, monkeypatch):
        """Test successful speedtest data fetch."""
        monkeypatch.setattr(Config, "SPEEDTEST_URL", "http://speedtest.local")
        monkeypatch.setattr(Config, "SPEEDTEST_TOKEN", "test_token_123")

        # Mock the API response
        responses.add(
            responses.GET,
            "http://speedtest.local/api/speedtest/latest",
            json=mock_speedtest_response,
            status=200,
        )

        client = SpeedtestClient()
        speedtest = client.get_latest()

        assert speedtest is not None
        assert speedtest.download == 245.67
        assert speedtest.upload == 89.12
        assert speedtest.ping == 12.5
        assert speedtest.server_name == "Example ISP"
        assert speedtest.server_host == "speedtest.example.com"
        assert speedtest.url == "http://www.speedtest.net/result/12345"
        assert "Nov 27" in speedtest.timestamp
        assert "2:30 PM" in speedtest.timestamp

    @responses.activate
    def test_get_latest_error_response(self, mock_error_response, monkeypatch):
        """Test handling of API error response."""
        monkeypatch.setattr(Config, "SPEEDTEST_URL", "http://speedtest.local")
        monkeypatch.setattr(Config, "SPEEDTEST_TOKEN", "invalid_token")

        responses.add(
            responses.GET,
            "http://speedtest.local/api/speedtest/latest",
            json=mock_error_response,
            status=200,
        )

        client = SpeedtestClient()
        speedtest = client.get_latest()

        assert speedtest is None

    @responses.activate
    def test_get_latest_missing_fields(self, mock_missing_fields_response, monkeypatch):
        """Test handling of response with missing required fields."""
        monkeypatch.setattr(Config, "SPEEDTEST_URL", "http://speedtest.local")
        monkeypatch.setattr(Config, "SPEEDTEST_TOKEN", "test_token")

        responses.add(
            responses.GET,
            "http://speedtest.local/api/speedtest/latest",
            json=mock_missing_fields_response,
            status=200,
        )

        client = SpeedtestClient()
        speedtest = client.get_latest()

        assert speedtest is None

    @responses.activate
    def test_get_latest_http_error(self, monkeypatch):
        """Test handling of HTTP error (401 Unauthorized)."""
        monkeypatch.setattr(Config, "SPEEDTEST_URL", "http://speedtest.local")
        monkeypatch.setattr(Config, "SPEEDTEST_TOKEN", "invalid_token")

        responses.add(
            responses.GET,
            "http://speedtest.local/api/speedtest/latest",
            json={"error": "Unauthorized"},
            status=401,
        )

        client = SpeedtestClient()
        speedtest = client.get_latest()

        assert speedtest is None

    @responses.activate
    def test_get_latest_malformed_json(self, monkeypatch):
        """Test handling of malformed JSON response."""
        monkeypatch.setattr(Config, "SPEEDTEST_URL", "http://speedtest.local")
        monkeypatch.setattr(Config, "SPEEDTEST_TOKEN", "test_token")

        responses.add(
            responses.GET,
            "http://speedtest.local/api/speedtest/latest",
            body="Not valid JSON",
            status=200,
        )

        client = SpeedtestClient()
        speedtest = client.get_latest()

        assert speedtest is None

    def test_initialization_missing_url(self, monkeypatch):
        """Test that missing URL raises ValueError."""
        monkeypatch.setattr(Config, "SPEEDTEST_URL", None)
        monkeypatch.setattr(Config, "SPEEDTEST_TOKEN", "test_token")

        with pytest.raises(ValueError, match="SPEEDTEST_URL must be configured"):
            SpeedtestClient()

    def test_initialization_missing_token(self, monkeypatch):
        """Test that missing token raises ValueError."""
        monkeypatch.setattr(Config, "SPEEDTEST_URL", "http://speedtest.local")
        monkeypatch.setattr(Config, "SPEEDTEST_TOKEN", None)

        with pytest.raises(ValueError, match="SPEEDTEST_TOKEN must be configured"):
            SpeedtestClient()

    @responses.activate
    def test_url_normalization_with_trailing_slash(self, mock_speedtest_response, monkeypatch):
        """Test that trailing slash in URL is handled correctly."""
        monkeypatch.setattr(Config, "SPEEDTEST_URL", "http://speedtest.local/")
        monkeypatch.setattr(Config, "SPEEDTEST_TOKEN", "test_token")

        # Should normalize to http://speedtest.local/api/speedtest/latest
        responses.add(
            responses.GET,
            "http://speedtest.local/api/speedtest/latest",
            json=mock_speedtest_response,
            status=200,
        )

        client = SpeedtestClient()
        speedtest = client.get_latest()

        assert speedtest is not None

    @responses.activate
    def test_timestamp_formatting_variants(self, monkeypatch):
        """Test various timestamp formats are handled correctly."""
        monkeypatch.setattr(Config, "SPEEDTEST_URL", "http://speedtest.local")
        monkeypatch.setattr(Config, "SPEEDTEST_TOKEN", "test_token")

        # Test with different timestamp format
        response_with_timestamp = {
            "message": "ok",
            "data": {
                "download": 100.0,
                "upload": 50.0,
                "ping": 10.0,
                "server_name": "Test",
                "server_host": "test.com",
                "created_at": "2025-01-05T09:15:30.000000Z",  # Single-digit hour/day
            },
        }

        responses.add(
            responses.GET,
            "http://speedtest.local/api/speedtest/latest",
            json=response_with_timestamp,
            status=200,
        )

        client = SpeedtestClient()
        speedtest = client.get_latest()

        assert speedtest is not None
        assert "Jan" in speedtest.timestamp
        assert "9:15 AM" in speedtest.timestamp

    @responses.activate
    def test_missing_timestamp(self, monkeypatch):
        """Test handling of missing timestamp field."""
        monkeypatch.setattr(Config, "SPEEDTEST_URL", "http://speedtest.local")
        monkeypatch.setattr(Config, "SPEEDTEST_TOKEN", "test_token")

        response_no_timestamp = {
            "message": "ok",
            "data": {
                "download": 100.0,
                "upload": 50.0,
                "ping": 10.0,
                "server_name": "Test",
                "server_host": "test.com",
                # No created_at field
            },
        }

        responses.add(
            responses.GET,
            "http://speedtest.local/api/speedtest/latest",
            json=response_no_timestamp,
            status=200,
        )

        client = SpeedtestClient()
        speedtest = client.get_latest()

        assert speedtest is not None
        assert speedtest.timestamp == "Unknown"

    @responses.activate
    def test_invalid_timestamp_format(self, monkeypatch):
        """Test handling of invalid timestamp format."""
        monkeypatch.setattr(Config, "SPEEDTEST_URL", "http://speedtest.local")
        monkeypatch.setattr(Config, "SPEEDTEST_TOKEN", "test_token")

        response_bad_timestamp = {
            "message": "ok",
            "data": {
                "download": 100.0,
                "upload": 50.0,
                "ping": 10.0,
                "server_name": "Test",
                "server_host": "test.com",
                "created_at": "invalid-timestamp",
            },
        }

        responses.add(
            responses.GET,
            "http://speedtest.local/api/speedtest/latest",
            json=response_bad_timestamp,
            status=200,
        )

        client = SpeedtestClient()
        speedtest = client.get_latest()

        assert speedtest is not None
        assert speedtest.timestamp == "Unknown"

    @responses.activate
    def test_optional_url_field(self, monkeypatch):
        """Test that URL field is optional in response."""
        monkeypatch.setattr(Config, "SPEEDTEST_URL", "http://speedtest.local")
        monkeypatch.setattr(Config, "SPEEDTEST_TOKEN", "test_token")

        response_no_url = {
            "message": "ok",
            "data": {
                "download": 100.0,
                "upload": 50.0,
                "ping": 10.0,
                "server_name": "Test",
                "server_host": "test.com",
                "created_at": "2025-11-27T14:30:00.000000Z",
                # No url field
            },
        }

        responses.add(
            responses.GET,
            "http://speedtest.local/api/speedtest/latest",
            json=response_no_url,
            status=200,
        )

        client = SpeedtestClient()
        speedtest = client.get_latest()

        assert speedtest is not None
        assert speedtest.url is None
