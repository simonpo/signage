"""
Tests for StockClient with mocked HTTP responses.
"""

import pytest
import responses

from src.clients.stock import StockClient
from src.config import Config


@pytest.fixture
def mock_stock_response():
    """Sample Alpha Vantage Global Quote API response."""
    return {
        "Global Quote": {
            "01. symbol": "AAPL",
            "02. open": "189.5000",
            "03. high": "191.2000",
            "04. low": "188.7500",
            "05. price": "190.6400",
            "06. volume": "45678910",
            "07. latest trading day": "2025-11-27",
            "08. previous close": "188.9500",
            "09. change": "1.6900",
            "10. change percent": "0.8945%",
        }
    }


@pytest.fixture
def mock_empty_response():
    """Empty response (API error or invalid symbol)."""
    return {
        "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute."
    }


@pytest.fixture
def mock_error_response():
    """Error response from Alpha Vantage."""
    return {"Error Message": "Invalid API call. Please retry or visit the documentation."}


class TestStockClient:
    """Test StockClient with mocked API responses."""

    @responses.activate
    def test_get_quote_success(self, mock_stock_response, monkeypatch):
        """Test successful stock quote fetch."""
        monkeypatch.setattr(Config, "STOCK_API_KEY", "test_api_key")
        monkeypatch.setattr(Config, "STOCK_SYMBOL", "AAPL")

        # Mock the API response
        responses.add(
            responses.GET,
            "https://www.alphavantage.co/query",
            json=mock_stock_response,
            status=200,
        )

        client = StockClient()
        stock = client.get_quote()

        assert stock is not None
        assert stock.symbol == "AAPL"
        assert stock.price == "190.6400"
        assert stock.change_percent == "0.8945%"

    @responses.activate
    def test_get_quote_empty_response(self, mock_empty_response, monkeypatch):
        """Test handling of empty Global Quote (rate limit or invalid symbol)."""
        monkeypatch.setattr(Config, "STOCK_API_KEY", "test_api_key")
        monkeypatch.setattr(Config, "STOCK_SYMBOL", "INVALID")

        responses.add(
            responses.GET,
            "https://www.alphavantage.co/query",
            json=mock_empty_response,
            status=200,
        )

        client = StockClient()
        stock = client.get_quote()

        assert stock is None

    @responses.activate
    def test_get_quote_error_response(self, mock_error_response, monkeypatch):
        """Test handling of API error response."""
        monkeypatch.setattr(Config, "STOCK_API_KEY", "invalid_key")
        monkeypatch.setattr(Config, "STOCK_SYMBOL", "AAPL")

        responses.add(
            responses.GET,
            "https://www.alphavantage.co/query",
            json=mock_error_response,
            status=200,
        )

        client = StockClient()
        stock = client.get_quote()

        assert stock is None

    @responses.activate
    def test_get_quote_http_error(self, monkeypatch):
        """Test handling of HTTP error (500)."""
        monkeypatch.setattr(Config, "STOCK_API_KEY", "test_api_key")
        monkeypatch.setattr(Config, "STOCK_SYMBOL", "AAPL")

        responses.add(
            responses.GET,
            "https://www.alphavantage.co/query",
            json={"error": "Internal server error"},
            status=500,
        )

        client = StockClient()
        stock = client.get_quote()

        assert stock is None

    def test_get_quote_missing_api_key(self, monkeypatch):
        """Test that missing API key returns None gracefully."""
        monkeypatch.setattr(Config, "STOCK_API_KEY", None)
        monkeypatch.setattr(Config, "STOCK_SYMBOL", "AAPL")

        client = StockClient()
        stock = client.get_quote()

        assert stock is None

    def test_get_quote_missing_symbol(self, monkeypatch):
        """Test that missing symbol returns None gracefully."""
        monkeypatch.setattr(Config, "STOCK_API_KEY", "test_api_key")
        monkeypatch.setattr(Config, "STOCK_SYMBOL", None)

        client = StockClient()
        stock = client.get_quote()

        assert stock is None

    def test_initialization_warns_missing_config(self, monkeypatch, caplog):
        """Test that initialization logs warnings for missing config."""
        monkeypatch.setattr(Config, "STOCK_API_KEY", None)
        monkeypatch.setattr(Config, "STOCK_SYMBOL", None)

        StockClient()

        assert "STOCK_API_KEY not configured" in caplog.text
        assert "STOCK_SYMBOL not configured" in caplog.text

    @responses.activate
    def test_get_quote_malformed_json(self, monkeypatch):
        """Test handling of malformed JSON response."""
        monkeypatch.setattr(Config, "STOCK_API_KEY", "test_api_key")
        monkeypatch.setattr(Config, "STOCK_SYMBOL", "AAPL")

        responses.add(
            responses.GET,
            "https://www.alphavantage.co/query",
            body="Not valid JSON",
            status=200,
        )

        client = StockClient()
        stock = client.get_quote()

        assert stock is None

    @responses.activate
    def test_get_quote_missing_fields(self, monkeypatch):
        """Test handling of response with missing fields."""
        monkeypatch.setattr(Config, "STOCK_API_KEY", "test_api_key")
        monkeypatch.setattr(Config, "STOCK_SYMBOL", "AAPL")

        # Response with incomplete data
        incomplete_response = {
            "Global Quote": {
                "01. symbol": "AAPL",
                # Missing price and change_percent
            }
        }

        responses.add(
            responses.GET,
            "https://www.alphavantage.co/query",
            json=incomplete_response,
            status=200,
        )

        client = StockClient()
        stock = client.get_quote()

        assert stock is not None
        assert stock.symbol == "AAPL"
        assert stock.price == "N/A"
        assert stock.change_percent == "N/A"
