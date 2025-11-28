"""
Tests for FerryClient with mocked HTTP responses.
"""

from datetime import datetime

import pytest
import responses

from src.clients.ferry import FerryClient, FerryWebScraper
from src.config import Config


@pytest.fixture
def mock_schedule_response():
    """Sample WSDOT ferry schedule response."""
    # API returns .NET date format: /Date(milliseconds-timezone)/
    future_time = int((datetime.now().timestamp() + 3600) * 1000)  # 1 hour from now
    past_time = int((datetime.now().timestamp() - 3600) * 1000)  # 1 hour ago

    return {
        "TerminalCombos": [
            {
                "DepartingTerminalName": "Fauntleroy",
                "ArrivingTerminalName": "Southworth",
                "Times": [
                    {
                        "DepartingTime": f"/Date({past_time}-0800)/",
                        "VesselName": "Tillikum",
                    },
                    {
                        "DepartingTime": f"/Date({future_time}-0800)/",
                        "VesselName": "Kennewick",
                    },
                ],
            },
            {
                "DepartingTerminalName": "Southworth",
                "ArrivingTerminalName": "Fauntleroy",
                "Times": [
                    {
                        "DepartingTime": f"/Date({future_time + 1800000}-0800)/",
                        "VesselName": "Issaquah",
                    },
                ],
            },
        ]
    }


@pytest.fixture
def mock_vessels_response():
    """Sample WSDOT vessel locations response."""
    return [
        {
            "VesselName": "Kennewick",
            "RouteID": 13,
            "Latitude": 47.5234,
            "Longitude": -122.5321,
            "Speed": 12.5,
            "Heading": 180,
        },
        {
            "VesselName": "Tillikum",
            "RouteID": 13,
            "Latitude": 47.5123,
            "Longitude": -122.5456,
            "Speed": 0.0,
            "Heading": 0,
        },
        {
            "VesselName": "Walla Walla",
            "RouteID": 5,  # Different route
            "Latitude": 48.1234,
            "Longitude": -122.7654,
            "Speed": 15.0,
            "Heading": 90,
        },
    ]


@pytest.fixture
def mock_alerts_response():
    """Sample WSDOT alerts response."""
    return [
        {
            "RouteID": 13,
            "BulletinTitle": "Normal service",
        },
        {
            "RouteID": 5,
            "BulletinTitle": "Cancelled due to weather",
        },
    ]


class TestFerryClient:
    """Test FerryClient with mocked API responses."""

    @responses.activate
    def test_get_ferry_data_success(
        self,
        monkeypatch,
        mock_schedule_response,
        mock_vessels_response,
        mock_alerts_response,
    ):
        """Test successful ferry data fetch."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "FERRY_HOME_TERMINAL", "Fauntleroy")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "test_key")

        today = datetime.now().strftime("%Y-%m-%d")

        # Mock schedule request
        responses.add(
            responses.GET,
            f"https://www.wsdot.wa.gov/Ferries/API/Schedule/rest/schedule/{today}/13",
            json=mock_schedule_response,
            status=200,
        )

        # Mock vessel locations
        responses.add(
            responses.GET,
            "https://www.wsdot.wa.gov/Ferries/API/Vessels/rest/vessellocations",
            json=mock_vessels_response,
            status=200,
        )

        # Mock alerts
        responses.add(
            responses.GET,
            "https://www.wsdot.wa.gov/Ferries/API/Schedule/rest/alerts",
            json=mock_alerts_response,
            status=200,
        )

        client = FerryClient()
        data = client.get_ferry_data()

        assert data is not None
        assert data.route == "Fauntleroy-Southworth"
        assert data.status == "normal"
        assert len(data.fauntleroy_departures) > 0
        assert len(data.vessels) == 2  # Only route 13 vessels

    @responses.activate
    def test_no_api_key_returns_stub(self, monkeypatch):
        """Test that missing API key returns stub data."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "FERRY_HOME_TERMINAL", "Fauntleroy")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", None)

        client = FerryClient()
        data = client.get_ferry_data()

        assert data is not None
        assert data.route == "Fauntleroy-Southworth"
        assert data.status == "normal"
        assert data.southworth_departures == []
        assert data.fauntleroy_departures == []

    @responses.activate
    def test_parse_dotnet_date(self, monkeypatch):
        """Test .NET date format parsing."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "test_key")

        client = FerryClient()

        # Test valid date
        dt, time_str = client._parse_dotnet_date("/Date(1700000000000-0800)/")
        assert dt is not None
        assert ":" in time_str
        assert "AM" in time_str or "PM" in time_str

        # Test invalid date
        dt, time_str = client._parse_dotnet_date("invalid")
        assert dt is None
        assert time_str == ""

    @responses.activate
    def test_vessels_filters_by_route(
        self, monkeypatch, mock_vessels_response
    ):
        """Test vessel filtering by route ID."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "test_key")

        responses.add(
            responses.GET,
            "https://www.wsdot.wa.gov/Ferries/API/Vessels/rest/vessellocations",
            json=mock_vessels_response,
            status=200,
        )

        client = FerryClient()
        vessels = client._get_vessel_locations()

        # Should only include route 13 vessels
        assert len(vessels) == 2
        vessel_names = [v.name for v in vessels]
        assert "Kennewick" in vessel_names
        assert "Tillikum" in vessel_names
        assert "Walla Walla" not in vessel_names

    @responses.activate
    def test_vessels_skips_invalid_coords(self, monkeypatch):
        """Test vessels without coordinates are skipped."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "test_key")

        invalid_response = [
            {
                "VesselName": "NoCoords",
                "RouteID": 13,
                "Latitude": None,
                "Longitude": None,
            },
        ]

        responses.add(
            responses.GET,
            "https://www.wsdot.wa.gov/Ferries/API/Vessels/rest/vessellocations",
            json=invalid_response,
            status=200,
        )

        client = FerryClient()
        vessels = client._get_vessel_locations()

        assert len(vessels) == 0

    @responses.activate
    def test_alerts_filters_by_route(self, monkeypatch, mock_alerts_response):
        """Test alerts filtering by route ID."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "test_key")

        responses.add(
            responses.GET,
            "https://www.wsdot.wa.gov/Ferries/API/Schedule/rest/alerts",
            json=mock_alerts_response,
            status=200,
        )

        client = FerryClient()
        alerts = client._get_alerts()

        # Should only include route 13 alerts
        assert len(alerts) == 1
        assert "Normal service" in alerts[0]

    @responses.activate
    def test_parse_status_from_alerts(self, monkeypatch):
        """Test status and delay parsing from alerts."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "test_key")

        client = FerryClient()

        # Test normal status
        status, delay = client._parse_status_from_alerts(["Normal service"])
        assert status == "normal"
        assert delay == 0

        # Test delay with minutes
        status, delay = client._parse_status_from_alerts(["Delayed 15 min"])
        assert status == "delayed"
        assert delay == 15

        # Test cancellation
        status, delay = client._parse_status_from_alerts(["Cancelled due to weather"])
        assert status == "cancelled"

    @responses.activate
    def test_get_all_vessel_locations(self, monkeypatch):
        """Test fetching all vessel locations system-wide."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "test_key")

        all_vessels = [
            {
                "VesselName": "Kennewick",
                "Latitude": 47.5234,
                "Longitude": -122.5321,
                "Speed": 12.5,
                "Heading": 180,
            },
            {
                "VesselName": "Walla Walla",
                "Latitude": 48.1234,
                "Longitude": -122.7654,
                "Speed": 15.0,
                "Heading": 90,
            },
            {
                "VesselName": "Invalid",
                "Latitude": 0,
                "Longitude": 0,  # Should be filtered out
                "Speed": 0,
                "Heading": 0,
            },
        ]

        responses.add(
            responses.GET,
            "https://www.wsdot.wa.gov/Ferries/API/Vessels/rest/vessellocations",
            json=all_vessels,
            status=200,
        )

        client = FerryClient()
        map_data = client.get_all_vessel_locations()

        assert map_data is not None
        assert len(map_data.vessels) == 2  # Excludes 0,0 vessel
        assert map_data.timestamp is not None

    @responses.activate
    def test_api_failure_returns_none(self, monkeypatch):
        """Test API failure handling."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "test_key")

        today = datetime.now().strftime("%Y-%m-%d")

        # Mock 500 error
        responses.add(
            responses.GET,
            f"https://www.wsdot.wa.gov/Ferries/API/Schedule/rest/schedule/{today}/13",
            json={"error": "internal_error"},
            status=500,
        )

        responses.add(
            responses.GET,
            "https://www.wsdot.wa.gov/Ferries/API/Vessels/rest/vessellocations",
            json=[],
            status=200,
        )

        responses.add(
            responses.GET,
            "https://www.wsdot.wa.gov/Ferries/API/Schedule/rest/alerts",
            json=[],
            status=200,
        )

        client = FerryClient()
        data = client.get_ferry_data()

        # Should return data even if schedule fails (empty sailings)
        assert data is not None

    @responses.activate
    def test_schedule_filters_past_sailings(
        self, monkeypatch, mock_schedule_response
    ):
        """Test that past sailings are filtered out."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "test_key")

        today = datetime.now().strftime("%Y-%m-%d")

        responses.add(
            responses.GET,
            f"https://www.wsdot.wa.gov/Ferries/API/Schedule/rest/schedule/{today}/13",
            json=mock_schedule_response,
            status=200,
        )

        client = FerryClient()
        schedule = client._get_schedule(today)

        # Should only include future sailings (2 from our fixture)
        assert len(schedule) == 2
        for sailing in schedule:
            assert sailing.departure_time != ""


class TestFerryWebScraper:
    """Test FerryWebScraper stub."""

    def test_scraper_not_implemented(self):
        """Test web scraper stub behavior."""
        scraper = FerryWebScraper()
        data = scraper.get_ferry_data()

        assert data is None
