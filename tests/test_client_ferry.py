"""
Tests for FerryClient with mocked HTTP responses.
"""

from datetime import datetime

import pytest
import responses

from src.clients.ferry import FerryClient
from src.config import Config


@pytest.fixture
def mock_schedule_response():
    """Sample WSDOT ferry schedule response."""
    # Use future timestamps (current time + 1 hour, + 2 hours, + 3 hours)
    now_ms = int(datetime.now().timestamp() * 1000)
    future_1h = now_ms + (3600 * 1000)
    future_2h = now_ms + (7200 * 1000)
    future_3h = now_ms + (10800 * 1000)

    return {
        "TerminalCombos": [
            {
                "DepartingTerminalID": 9,
                "DepartingTerminalName": "Fauntleroy",
                "ArrivingTerminalID": 20,
                "ArrivingTerminalName": "Southworth",
                "Times": [
                    {
                        "DepartingTime": f"/Date({future_1h}-0800)/",
                        "ArrivingTime": f"/Date({future_1h + 1800000}-0800)/",
                        "VesselName": "Issaquah",
                    },
                    {
                        "DepartingTime": f"/Date({future_2h}-0800)/",
                        "ArrivingTime": f"/Date({future_2h + 1800000}-0800)/",
                        "VesselName": "Kitsap",
                    },
                ],
            },
            {
                "DepartingTerminalID": 20,
                "DepartingTerminalName": "Southworth",
                "ArrivingTerminalID": 9,
                "ArrivingTerminalName": "Fauntleroy",
                "Times": [
                    {
                        "DepartingTime": f"/Date({future_3h}-0800)/",
                        "ArrivingTime": f"/Date({future_3h + 1800000}-0800)/",
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
            "VesselID": 1,
            "VesselName": "Issaquah",
            "RouteID": 13,
            "Latitude": 47.5231,
            "Longitude": -122.4567,
            "Speed": 12.5,
            "Heading": 180,
        },
        {
            "VesselID": 2,
            "VesselName": "Kitsap",
            "RouteID": 13,
            "Latitude": 47.5089,
            "Longitude": -122.4712,
            "Speed": 0.0,
            "Heading": 90,
        },
        {
            "VesselID": 3,
            "VesselName": "Other Ferry",
            "RouteID": 5,  # Different route
            "Latitude": 48.1234,
            "Longitude": -122.9876,
            "Speed": 10.0,
            "Heading": 270,
        },
    ]


@pytest.fixture
def mock_alerts_response():
    """Sample WSDOT alerts response."""
    return [
        {
            "BulletinTitle": "15 minute delay due to heavy traffic",
            "RouteID": 13,
        },
        {
            "BulletinTitle": "Service operating normally",
            "RouteID": 7,  # Different route
        },
    ]


class TestFerryClient:
    """Test FerryClient with mocked API responses."""

    @responses.activate
    def test_init_requires_config(self, monkeypatch):
        """Test that client warns when configuration missing."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", None)
        monkeypatch.setattr(Config, "WSDOT_API_KEY", None)

        client = FerryClient()

        assert client.route is None
        assert client.api_key is None

    @responses.activate
    def test_get_ferry_data_success(
        self, monkeypatch, mock_schedule_response, mock_vessels_response, mock_alerts_response
    ):
        """Test successful ferry data fetch."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "FERRY_HOME_TERMINAL", "Fauntleroy")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "test_api_key")

        today = datetime.now().strftime("%Y-%m-%d")

        # Mock schedule request
        responses.add(
            responses.GET,
            f"https://www.wsdot.wa.gov/Ferries/API/Schedule/rest/schedule/{today}/13",
            json=mock_schedule_response,
            status=200,
        )

        # Mock vessels request
        responses.add(
            responses.GET,
            "https://www.wsdot.wa.gov/Ferries/API/Vessels/rest/vessellocations",
            json=mock_vessels_response,
            status=200,
        )

        # Mock alerts request
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
        assert data.status == "delayed"
        assert data.delay_minutes == 15
        assert len(data.fauntleroy_departures) == 2
        assert len(data.southworth_departures) == 1
        assert len(data.vessels) == 2  # Only route 13 vessels
        assert len(data.alerts) == 1  # Only route 13 alerts

    @responses.activate
    def test_get_ferry_data_no_config(self, monkeypatch):
        """Test ferry data returns stub when not configured."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", None)
        monkeypatch.setattr(Config, "WSDOT_API_KEY", None)

        client = FerryClient()
        data = client.get_ferry_data()

        assert data is not None
        assert data.route == "Fauntleroy-Southworth"  # Default
        assert data.status == "normal"
        assert len(data.fauntleroy_departures) == 0
        assert len(data.southworth_departures) == 0

    @responses.activate
    def test_parse_dotnet_date(self, monkeypatch):
        """Test .NET date format parsing."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Test")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "key")

        client = FerryClient()

        # Test valid date
        dt, time_str = client._parse_dotnet_date("/Date(1732824900000-0800)/")
        assert dt is not None
        assert ":" in time_str
        assert "M" in time_str  # AM or PM

        # Test invalid date
        dt, time_str = client._parse_dotnet_date("invalid")
        assert dt is None
        assert time_str == ""

    @responses.activate
    def test_vessel_filtering_by_route(
        self, monkeypatch, mock_vessels_response
    ):
        """Test that only vessels on the configured route are included."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "test_api_key")

        responses.add(
            responses.GET,
            "https://www.wsdot.wa.gov/Ferries/API/Vessels/rest/vessellocations",
            json=mock_vessels_response,
            status=200,
        )

        client = FerryClient()
        vessels = client._get_vessel_locations()

        # Should only include route 13 vessels (Issaquah and Kitsap)
        assert len(vessels) == 2
        vessel_names = [v.name for v in vessels]
        assert "Issaquah" in vessel_names
        assert "Kitsap" in vessel_names
        assert "Other Ferry" not in vessel_names

    @responses.activate
    def test_alert_filtering_by_route(self, monkeypatch, mock_alerts_response):
        """Test that only alerts for the configured route are included."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "test_api_key")

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
        assert "15 minute delay" in alerts[0]

    @responses.activate
    def test_status_parsing_cancelled(self, monkeypatch):
        """Test status parsing for cancelled service."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Test")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "key")

        client = FerryClient()

        alerts = ["Service cancelled due to weather"]
        status, delay = client._parse_status_from_alerts(alerts)

        assert status == "cancelled"
        assert delay == 0

    @responses.activate
    def test_status_parsing_delay_with_minutes(self, monkeypatch):
        """Test status parsing extracts delay minutes."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Test")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "key")

        client = FerryClient()

        alerts = ["30 min delay due to mechanical issue"]
        status, delay = client._parse_status_from_alerts(alerts)

        assert status == "delayed"
        assert delay == 30

    @responses.activate
    def test_api_error_handling(self, monkeypatch):
        """Test handling of API errors."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "test_api_key")

        today = datetime.now().strftime("%Y-%m-%d")

        # Mock 500 error for schedule
        responses.add(
            responses.GET,
            f"https://www.wsdot.wa.gov/Ferries/API/Schedule/rest/schedule/{today}/13",
            json={"error": "internal server error"},
            status=500,
        )

        # Mock 404 for vessels
        responses.add(
            responses.GET,
            "https://www.wsdot.wa.gov/Ferries/API/Vessels/rest/vessellocations",
            status=404,
        )

        # Mock timeout for alerts
        responses.add(
            responses.GET,
            "https://www.wsdot.wa.gov/Ferries/API/Schedule/rest/alerts",
            body=Exception("Connection timeout"),
        )

        client = FerryClient()
        data = client.get_ferry_data()

        # Should return partial data with empty lists when APIs fail
        assert data is not None
        assert data.route == "Fauntleroy-Southworth"
        assert len(data.fauntleroy_departures) == 0
        assert len(data.vessels) == 0
        assert len(data.alerts) == 0

    @responses.activate
    def test_get_all_vessel_locations(self, monkeypatch):
        """Test fetching all vessel locations across the system."""
        monkeypatch.setattr(Config, "FERRY_ROUTE", "Fauntleroy-Southworth")
        monkeypatch.setattr(Config, "WSDOT_API_KEY", "test_api_key")

        # Mock with vessels from multiple routes
        all_vessels = [
            {
                "VesselName": "Issaquah",
                "RouteID": 13,
                "Latitude": 47.5231,
                "Longitude": -122.4567,
                "Speed": 12.5,
                "Heading": 180,
            },
            {
                "VesselName": "Tacoma",
                "RouteID": 5,
                "Latitude": 47.6062,
                "Longitude": -122.3321,
                "Speed": 15.0,
                "Heading": 90,
            },
            {
                "VesselName": "Invalid",
                "RouteID": 7,
                "Latitude": 0,  # Invalid location
                "Longitude": 0,
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
        assert len(map_data.vessels) == 2  # Excludes vessel at 0,0
        vessel_names = [v.name for v in map_data.vessels]
        assert "Issaquah" in vessel_names
        assert "Tacoma" in vessel_names
        assert "Invalid" not in vessel_names
