"""
Tests for TeslaFleetClient with mocked HTTP responses.
"""

import json
from datetime import datetime, timedelta

import pytest
import requests
import responses

from src.clients.tesla_fleet import TeslaFleetClient
from src.config import Config


@pytest.fixture
def mock_token_response():
    """Sample Tesla OAuth token response."""
    return {
        "access_token": "test_access_token_abc123",
        "token_type": "Bearer",
        "expires_in": 3600,
    }


@pytest.fixture
def mock_vehicles_response():
    """Sample Tesla vehicles list response."""
    return {
        "response": [
            {
                "id": 12345678901234567,
                "vehicle_id": 123456789,
                "vin": "5YJ3E1EA1JF000001",
                "display_name": "Model Y",
                "state": "online",
            }
        ]
    }


@pytest.fixture
def mock_vehicle_data_response():
    """Sample Tesla vehicle data response."""
    return {
        "response": {
            "id": 12345678901234567,
            "vehicle_id": 123456789,
            "display_name": "Model Y",
            "state": "online",
            "charge_state": {
                "battery_level": 86,
                "battery_range": 222.5,
                "charge_limit_soc": 90,
                "charging_state": "Disconnected",
                "time_to_full_charge": 0.0,
                "charger_power": 0,
            },
            "climate_state": {
                "inside_temp": 20.5,
                "outside_temp": 12.8,
                "is_climate_on": True,
                "is_front_defroster_on": False,
            },
            "vehicle_state": {
                "car_version": "2024.26.9",
                "locked": True,
                "sentry_mode": False,
                "odometer": 12543.2,
            },
            "drive_state": {
                "latitude": 47.6062,
                "longitude": -122.3321,
                "heading": 180,
                "shift_state": None,
                "speed": None,
            },
        }
    }


@pytest.fixture
def temp_token_file(tmp_path):
    """Create temporary token file."""
    token_file = tmp_path / ".tesla_tokens.json"
    return token_file


class TestTeslaFleetClient:
    """Test TeslaFleetClient with mocked API responses."""

    @responses.activate
    def test_init_requires_credentials(self, monkeypatch):
        """Test that client requires Tesla credentials."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", None)
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", None)

        with pytest.raises(ValueError, match="TESLA_CLIENT_ID and TESLA_CLIENT_SECRET"):
            TeslaFleetClient()

    @responses.activate
    def test_init_success(self, monkeypatch, temp_token_file):
        """Test successful client initialization."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(Config, "TESLA_REGION", "na")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        client = TeslaFleetClient()

        assert client.client_id == "test_client_id"
        assert client.region == "na"
        assert client.base_url == "https://fleet-api.prd.na.vn.cloud.tesla.com"

    @responses.activate
    def test_get_vehicles_success(
        self, monkeypatch, temp_token_file, mock_token_response, mock_vehicles_response
    ):
        """Test successful vehicle list fetch."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(Config, "TESLA_REGION", "na")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        # Mock token request
        responses.add(
            responses.POST,
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            json=mock_token_response,
            status=200,
        )

        # Mock vehicles request
        responses.add(
            responses.GET,
            "https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/vehicles",
            json=mock_vehicles_response,
            status=200,
        )

        client = TeslaFleetClient()
        vehicles = client.get_vehicles()

        assert vehicles is not None
        assert len(vehicles) == 1
        assert vehicles[0]["display_name"] == "Model Y"
        assert vehicles[0]["state"] == "online"

    @responses.activate
    def test_get_vehicle_data_success(
        self, monkeypatch, temp_token_file, mock_token_response, mock_vehicle_data_response
    ):
        """Test successful vehicle data fetch."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        # Mock token request
        responses.add(
            responses.POST,
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            json=mock_token_response,
            status=200,
        )

        # Mock vehicle data request
        vehicle_id = 12345678901234567
        responses.add(
            responses.GET,
            f"https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/vehicles/{vehicle_id}/vehicle_data",
            json=mock_vehicle_data_response,
            status=200,
        )

        client = TeslaFleetClient()
        data = client.get_vehicle_data(vehicle_id)

        assert data is not None
        assert data["display_name"] == "Model Y"
        assert data["charge_state"]["battery_level"] == 86
        assert data["climate_state"]["is_climate_on"] is True
        assert data["vehicle_state"]["locked"] is True

    @responses.activate
    def test_token_refresh(self, monkeypatch, temp_token_file):
        """Test token refresh flow."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        # Save expired token
        expired_token = {
            "access_token": "old_token",
            "expires_at": (datetime.now() - timedelta(hours=1)).isoformat(),
            "refresh_token": "refresh_token_123",
        }
        with open(temp_token_file, "w") as f:
            json.dump(expired_token, f)

        # Mock refresh token request
        responses.add(
            responses.POST,
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            json={
                "access_token": "new_access_token",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
            status=200,
        )

        # Mock vehicles request to trigger token refresh
        responses.add(
            responses.GET,
            "https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/vehicles",
            json={"response": []},
            status=200,
        )

        client = TeslaFleetClient()
        assert client.access_token == "old_token"  # Loaded from file

        client.get_vehicles()

        # Token should be refreshed
        assert client.access_token == "new_access_token"

    @responses.activate
    def test_api_error_handling(self, monkeypatch, temp_token_file, mock_token_response):
        """Test handling of API errors."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        # Mock token request
        responses.add(
            responses.POST,
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            json=mock_token_response,
            status=200,
        )

        # Mock 404 error for vehicles
        responses.add(
            responses.GET,
            "https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/vehicles",
            json={"error": "not_found"},
            status=404,
        )

        client = TeslaFleetClient()
        vehicles = client.get_vehicles()

        assert vehicles is None

    @responses.activate
    def test_region_selection(self, monkeypatch, temp_token_file):
        """Test region endpoint selection."""
        test_cases = [
            ("na", "https://fleet-api.prd.na.vn.cloud.tesla.com"),
            ("eu", "https://fleet-api.prd.eu.vn.cloud.tesla.com"),
            ("cn", "https://fleet-api.prd.cn.vn.cloud.tesla.cn"),
        ]

        for region, expected_url in test_cases:
            monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
            monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
            monkeypatch.setattr(Config, "TESLA_REGION", region)
            monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

            client = TeslaFleetClient()
            assert client.base_url == expected_url

    def test_token_persistence(self, monkeypatch, temp_token_file):
        """Test token saving and loading."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        # Create client and save token
        client1 = TeslaFleetClient()
        client1._save_tokens("test_token_123", 3600)

        # Create new client and verify token loaded
        client2 = TeslaFleetClient()
        assert client2.access_token == "test_token_123"
        assert client2.token_expires_at is not None

    @responses.activate
    def test_token_persistence_with_refresh(self, monkeypatch, temp_token_file):
        """Test token saving and loading with refresh token."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        client = TeslaFleetClient()
        client._save_tokens("access_token_123", 3600, "refresh_token_456")

        # Verify both tokens saved
        with open(temp_token_file) as f:
            data = json.load(f)
        assert data["access_token"] == "access_token_123"
        assert data["refresh_token"] == "refresh_token_456"
        assert "expires_at" in data

    @responses.activate
    def test_client_credentials_grant(self, monkeypatch, temp_token_file):
        """Test client_credentials grant type (no refresh token)."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        # Mock client_credentials token request
        responses.add(
            responses.POST,
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            json={
                "access_token": "client_creds_token",
                "token_type": "Bearer",
                "expires_in": 3600,
            },
            status=200,
        )

        # Mock vehicles request
        responses.add(
            responses.GET,
            "https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/vehicles",
            json={"response": []},
            status=200,
        )

        client = TeslaFleetClient()
        vehicles = client.get_vehicles()

        assert client.access_token == "client_creds_token"
        assert vehicles == []

    @responses.activate
    def test_failed_token_load(self, monkeypatch, temp_token_file):
        """Test handling of corrupted token file."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        # Write invalid JSON
        with open(temp_token_file, "w") as f:
            f.write("invalid json {")

        # Mock client_credentials request (fallback)
        responses.add(
            responses.POST,
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            json={"access_token": "new_token", "expires_in": 3600},
            status=200,
        )

        # Should not crash, should fall back to new token
        client = TeslaFleetClient()
        assert client.access_token is None  # Not loaded yet

    @responses.activate
    def test_get_energy_sites(self, monkeypatch, temp_token_file, mock_token_response):
        """Test energy sites API call."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        # Mock token request
        responses.add(
            responses.POST,
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            json=mock_token_response,
            status=200,
        )

        # Mock energy sites request
        responses.add(
            responses.GET,
            "https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/energy_sites",
            json={"response": [{"id": 67890, "site_name": "My Powerwall"}]},
            status=200,
        )

        client = TeslaFleetClient()
        sites = client.get_energy_sites()

        assert sites is not None
        assert len(sites) == 1
        assert sites[0]["site_name"] == "My Powerwall"

    @responses.activate
    def test_get_energy_site_data(self, monkeypatch, temp_token_file, mock_token_response):
        """Test energy site live status API call."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        # Mock token request
        responses.add(
            responses.POST,
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            json=mock_token_response,
            status=200,
        )

        # Mock energy site data request
        site_id = 67890
        responses.add(
            responses.GET,
            f"https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/energy_sites/{site_id}/live_status",
            json={
                "response": {
                    "solar_power": 5200,
                    "battery_power": -1500,
                    "grid_power": 0,
                    "percentage_charged": 95.5,
                }
            },
            status=200,
        )

        client = TeslaFleetClient()
        data = client.get_energy_site_data(site_id)

        assert data is not None
        assert data["solar_power"] == 5200
        assert data["percentage_charged"] == 95.5

    @responses.activate
    def test_api_error_with_status_code(self, monkeypatch, temp_token_file, mock_token_response):
        """Test API error handling with non-200 status."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        # Mock token request
        responses.add(
            responses.POST,
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            json=mock_token_response,
            status=200,
        )

        # Mock 500 error
        responses.add(
            responses.GET,
            "https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/vehicles",
            json={"error": "internal_error"},
            status=500,
        )

        client = TeslaFleetClient()
        vehicles = client.get_vehicles()

        assert vehicles is None

    @responses.activate
    def test_failed_token_refresh_fallback(self, monkeypatch, temp_token_file):
        """Test fallback to client_credentials when refresh fails."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        # Save expired token with refresh token
        expired_token = {
            "access_token": "old_token",
            "expires_at": (datetime.now() - timedelta(hours=1)).isoformat(),
            "refresh_token": "bad_refresh_token",
        }
        with open(temp_token_file, "w") as f:
            json.dump(expired_token, f)

        # Mock failed refresh token request
        responses.add(
            responses.POST,
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            json={"error": "invalid_grant"},
            status=400,
        )

        # Mock successful client_credentials request (fallback)
        responses.add(
            responses.POST,
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            json={"access_token": "fallback_token", "expires_in": 3600},
            status=200,
        )

        # Mock vehicles request
        responses.add(
            responses.GET,
            "https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/vehicles",
            json={"response": []},
            status=200,
        )

        client = TeslaFleetClient()
        vehicles = client.get_vehicles()

        assert client.access_token == "fallback_token"
        assert vehicles == []

    def test_token_save_failure(self, monkeypatch, tmp_path):
        """Test handling of token save failures."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")

        # Use a read-only directory to trigger write failure
        readonly_file = tmp_path / "readonly" / ".tesla_tokens.json"
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", readonly_file)

        client = TeslaFleetClient()
        # Should not crash, just log warning
        client._save_tokens("test_token", 3600)

        # Token should still be in memory even if save failed
        assert client.access_token == "test_token"

    @responses.activate
    def test_complete_token_failure(self, monkeypatch, temp_token_file):
        """Test complete failure to obtain token raises exception."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        # Mock failed token request
        responses.add(
            responses.POST,
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            json={"error": "invalid_client"},
            status=401,
        )

        # Mock vehicles request to trigger token fetch
        responses.add(
            responses.GET,
            "https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/vehicles",
            json={"response": []},
            status=200,
        )

        client = TeslaFleetClient()

        # Should raise exception when token fetch completely fails
        with pytest.raises(requests.exceptions.HTTPError):
            client.get_vehicles()

    @responses.activate
    def test_token_refresh_success(self, monkeypatch, temp_token_file):
        """Test successful token refresh with new refresh token."""
        monkeypatch.setattr(Config, "TESLA_CLIENT_ID", "test_client_id")
        monkeypatch.setattr(Config, "TESLA_CLIENT_SECRET", "test_client_secret")
        monkeypatch.setattr(TeslaFleetClient, "TOKEN_FILE", temp_token_file)

        # Save expired token with refresh token
        expired_token = {
            "access_token": "old_token",
            "expires_at": (datetime.now() - timedelta(hours=1)).isoformat(),
            "refresh_token": "valid_refresh_token",
        }
        with open(temp_token_file, "w") as f:
            json.dump(expired_token, f)

        # Mock successful refresh with new refresh token
        responses.add(
            responses.POST,
            "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token",
            json={
                "access_token": "refreshed_token",
                "expires_in": 3600,
                "refresh_token": "new_refresh_token",
            },
            status=200,
        )

        # Mock vehicles request
        responses.add(
            responses.GET,
            "https://fleet-api.prd.na.vn.cloud.tesla.com/api/1/vehicles",
            json={"response": []},
            status=200,
        )

        client = TeslaFleetClient()
        client.get_vehicles()

        # Verify token was refreshed and new refresh token saved
        assert client.access_token == "refreshed_token"
        assert client.refresh_token == "new_refresh_token"

        # Check file has new refresh token
        with open(temp_token_file) as f:
            data = json.load(f)
        assert data["refresh_token"] == "new_refresh_token"
