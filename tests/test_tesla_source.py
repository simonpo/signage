"""
Tests for TeslaSource plugin with focus on new data extraction logic.
"""

from unittest.mock import Mock, patch

import pytest

from src.plugins.sources.tesla_source import TeslaSource


@pytest.fixture
def mock_vehicle_data():
    """Complete mock vehicle data response from Tesla API."""
    return {
        "id": 12345678901234567,
        "display_name": "Model Y",
        "state": "online",
        "charge_state": {
            "battery_level": 86,
            "battery_range": 222.5,
            "charge_limit_soc": 90,
            "charging_state": "Disconnected",
            "time_to_full_charge": 0.0,
            "charger_power": 0,
            "conn_charge_cable": "Disconnected",
            "charge_port_door_open": False,
        },
        "climate_state": {
            "inside_temp": 20.5,
            "outside_temp": 12.8,
            "is_climate_on": True,
            "defrost_mode": 0,
        },
        "vehicle_state": {
            "car_version": "2024.44.3 abc123def456",
            "locked": True,
            "sentry_mode": False,
            "odometer": 20002.4,
            "tpms_pressure_fl": 2.9,
            "tpms_pressure_fr": 2.9,
            "tpms_pressure_rl": 2.9,
            "tpms_pressure_rr": 2.9,
        },
        "drive_state": {
            "latitude": 47.6062,
            "longitude": -122.3321,
            "heading": 180,
            "shift_state": None,
            "speed": None,
        },
        "vehicle_config": {
            "car_type": "modely",
        },
    }


@pytest.fixture
def mock_config():
    """Mock config for TeslaSource."""
    return {"vehicle_index": 0}


class TestTeslaSource:
    """Test TeslaSource plugin with focus on new data extraction."""

    def test_validate_config_valid(self, mock_config):
        """Test config validation with valid config."""
        source = TeslaSource("tesla_test", mock_config)
        assert source.validate_config() is True

    def test_validate_config_negative_index(self):
        """Test config validation rejects negative index."""
        source = TeslaSource("tesla_test", {"vehicle_index": -1})
        with pytest.raises(ValueError, match="non-negative integer"):
            source.validate_config()

    def test_validate_config_invalid_type(self):
        """Test config validation rejects non-integer index."""
        source = TeslaSource("tesla_test", {"vehicle_index": "zero"})
        with pytest.raises(ValueError, match="non-negative integer"):
            source.validate_config()

    def test_validate_config_no_index(self):
        """Test config validation succeeds with no index (defaults to 0)."""
        source = TeslaSource("tesla_test", {})
        assert source.validate_config() is True

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_fetch_data_success(self, mock_client_class, mock_config, mock_vehicle_data):
        """Test successful data fetch with all fields."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = [
            {"id": 12345678901234567, "display_name": "Model Y", "state": "online"}
        ]
        mock_client.get_vehicle_data.return_value = mock_vehicle_data
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()
        assert result is not None

        assert result is not None
        assert result.layout_type == "modern_tesla"
        tesla_data = result.metadata["tesla_data"]
        assert tesla_data.vehicle_name == "Model Y"
        assert tesla_data.battery_level == "86"
        assert tesla_data.range == "222"

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_software_version_extraction(self, mock_client_class, mock_config, mock_vehicle_data):
        """Test software version extracts only version number, not VIN."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "online"}
        ]

        # car_version format: "2024.44.3 abc123def456" (version + hash/VIN)
        mock_vehicle_data["vehicle_state"]["car_version"] = "2024.44.3 180D40230309"
        mock_client.get_vehicle_data.return_value = mock_vehicle_data
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()
        assert result is not None

        # Should extract only "2024.44.3", not the VIN part
        tesla_data = result.metadata["tesla_data"]
        assert tesla_data.software_version == "2024.44.3"
        assert "180D40230309" not in tesla_data.software_version

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_tire_pressure_conversion(self, mock_client_class, mock_config, mock_vehicle_data):
        """Test tire pressure converts bar to PSI correctly."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "online"}
        ]

        # Set tire pressures in bar
        mock_vehicle_data["vehicle_state"]["tpms_pressure_fl"] = 2.9
        mock_vehicle_data["vehicle_state"]["tpms_pressure_fr"] = 3.0
        mock_vehicle_data["vehicle_state"]["tpms_pressure_rl"] = 2.8
        mock_vehicle_data["vehicle_state"]["tpms_pressure_rr"] = 2.85

        mock_client.get_vehicle_data.return_value = mock_vehicle_data
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()
        assert result is not None

        tire_pressure = result.metadata["tesla_data"].tire_pressure

        # 2.9 bar × 14.5038 ≈ 42.1 PSI
        assert tire_pressure["front_left"] == pytest.approx(42.1, abs=0.1)
        assert tire_pressure["front_right"] == pytest.approx(43.5, abs=0.1)
        assert tire_pressure["rear_left"] == pytest.approx(40.6, abs=0.1)
        assert tire_pressure["rear_right"] == pytest.approx(41.3, abs=0.1)

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_plugged_in_detection_invalid(self, mock_client_class, mock_config, mock_vehicle_data):
        """Test plugged_in correctly handles <invalid> status."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "online"}
        ]

        # Test <invalid> status (vehicle asleep, unplugged)
        mock_vehicle_data["charge_state"]["conn_charge_cable"] = "<invalid>"
        mock_vehicle_data["charge_state"]["charge_port_door_open"] = False

        mock_client.get_vehicle_data.return_value = mock_vehicle_data
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()
        assert result is not None

        assert result.metadata["tesla_data"].plugged_in is False

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_plugged_in_detection_connected(
        self, mock_client_class, mock_config, mock_vehicle_data
    ):
        """Test plugged_in correctly detects connected cable."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "online"}
        ]

        # Plugged in with port open
        mock_vehicle_data["charge_state"]["conn_charge_cable"] = "IEC"
        mock_vehicle_data["charge_state"]["charge_port_door_open"] = True

        mock_client.get_vehicle_data.return_value = mock_vehicle_data
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()
        assert result is not None

        assert result.metadata["tesla_data"].plugged_in is True

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_plugged_in_detection_disconnected(
        self, mock_client_class, mock_config, mock_vehicle_data
    ):
        """Test plugged_in correctly handles Disconnected status."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "online"}
        ]

        mock_vehicle_data["charge_state"]["conn_charge_cable"] = "Disconnected"
        mock_vehicle_data["charge_state"]["charge_port_door_open"] = False

        mock_client.get_vehicle_data.return_value = mock_vehicle_data
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()
        assert result is not None

        assert result.metadata["tesla_data"].plugged_in is False

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_vehicle_type_formatting(self, mock_client_class, mock_config, mock_vehicle_data):
        """Test vehicle type formats correctly."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "online"}
        ]

        # Test different car types
        test_cases = [
            ("modely", "Model Y"),
            ("model3", "Model 3"),
            ("models", "Model S"),
            ("modelx", "Model X"),
        ]

        for car_type, expected in test_cases:
            mock_vehicle_data["vehicle_config"]["car_type"] = car_type
            mock_client.get_vehicle_data.return_value = mock_vehicle_data
            mock_client_class.return_value = mock_client

            source = TeslaSource("tesla_test", mock_config)
            result = source.fetch_data()
            assert result is not None

            assert result.metadata["tesla_data"].vehicle_type == expected

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_drive_state_null_handling(self, mock_client_class, mock_config, mock_vehicle_data):
        """Test drive state handles null values when parked."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "online"}
        ]

        # Null values when parked
        mock_vehicle_data["drive_state"]["latitude"] = None
        mock_vehicle_data["drive_state"]["longitude"] = None
        mock_vehicle_data["drive_state"]["heading"] = None
        mock_vehicle_data["drive_state"]["shift_state"] = None
        mock_vehicle_data["drive_state"]["speed"] = None

        mock_client.get_vehicle_data.return_value = mock_vehicle_data
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()
        assert result is not None

        # Should default to 0.0 / "" instead of crashing
        tesla_data = result.metadata["tesla_data"]
        assert tesla_data.latitude == 0.0
        assert tesla_data.longitude == 0.0
        assert tesla_data.heading == 0
        assert tesla_data.shift_state == ""
        assert tesla_data.speed == 0.0

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_last_updated_format(self, mock_client_class, mock_config, mock_vehicle_data):
        """Test last_updated timestamp has human-readable format."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "online"}
        ]
        mock_client.get_vehicle_data.return_value = mock_vehicle_data
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()
        assert result is not None

        # Should be like "November 30, 2025 at 01:23 PM"
        last_updated = result.metadata["tesla_data"].last_updated
        assert "at" in last_updated
        assert "20" in last_updated  # Year should be in format
        assert any(
            month in last_updated
            for month in [
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ]
        )

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_cached_data_handling(self, mock_client_class, mock_config, mock_vehicle_data):
        """Test cached data is used when vehicle is asleep."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "asleep"}
        ]

        # No live data available
        mock_client.get_vehicle_data.return_value = None

        # Cached data available
        mock_client.get_cached_vehicle_data.return_value = {
            "data": mock_vehicle_data,
            "cached_at": "2025-11-30T12:00:00",
        }
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()
        assert result is not None

        assert result is not None
        assert result.metadata["tesla_data"].cached_at == "2025-11-30T12:00:00"

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_no_vehicles_available(self, mock_client_class, mock_config):
        """Test handling when no vehicles are available."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = []
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()

        assert result is None

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_vehicle_index_out_of_range(self, mock_client_class):
        """Test handling when vehicle_index exceeds available vehicles."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "online"}
        ]
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", {"vehicle_index": 5})
        result = source.fetch_data()

        assert result is None

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_missing_tire_pressure_data(self, mock_client_class, mock_config, mock_vehicle_data):
        """Test handling when tire pressure data is missing."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "online"}
        ]

        # Remove tire pressure data
        del mock_vehicle_data["vehicle_state"]["tpms_pressure_fl"]

        mock_client.get_vehicle_data.return_value = mock_vehicle_data
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()
        assert result is not None

        # Should return empty dict instead of crashing
        assert result.metadata["tesla_data"].tire_pressure == {}

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_incomplete_vehicle_data(self, mock_client_class, mock_config):
        """Test handling of incomplete vehicle data (missing battery info)."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "online"}
        ]

        # Missing critical battery data
        incomplete_data: dict[str, dict[str, object]] = {
            "charge_state": {},  # Empty
            "climate_state": {},
            "vehicle_state": {},
            "drive_state": {},
            "vehicle_config": {},
        }

        mock_client.get_vehicle_data.return_value = incomplete_data
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()

        assert result is None

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_client_exception_handling(self, mock_client_class, mock_config):
        """Test exception handling when client raises error."""
        mock_client = Mock()
        mock_client.get_vehicles.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()

        assert result is None

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_defrost_mode_detection(self, mock_client_class, mock_config, mock_vehicle_data):
        """Test defrost mode detection (0 = off, 1+ = on)."""
        mock_client = Mock()
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "online"}
        ]

        # Test defrost off
        mock_vehicle_data["climate_state"]["defrost_mode"] = 0
        mock_client.get_vehicle_data.return_value = mock_vehicle_data
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()
        assert result is not None
        assert result.metadata["tesla_data"].defrost_on is False

        # Test defrost on
        mock_vehicle_data["climate_state"]["defrost_mode"] = 1
        mock_client.get_vehicle_data.return_value = mock_vehicle_data
        result = source.fetch_data()
        assert result is not None
        assert result.metadata["tesla_data"].defrost_on is True

    @patch("src.plugins.sources.tesla_source.TeslaFleetClient")
    def test_online_status_detection(self, mock_client_class, mock_config, mock_vehicle_data):
        """Test online/offline status detection."""
        mock_client = Mock()

        # Test online
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "online"}
        ]
        mock_client.get_vehicle_data.return_value = mock_vehicle_data
        mock_client_class.return_value = mock_client

        source = TeslaSource("tesla_test", mock_config)
        result = source.fetch_data()
        assert result is not None
        assert result.metadata["tesla_data"].online is True

        # Test offline
        mock_client.get_vehicles.return_value = [
            {"id": 123, "display_name": "Model Y", "state": "offline"}
        ]
        result = source.fetch_data()
        assert result is not None
        assert result.metadata["tesla_data"].online is False
