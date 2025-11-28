"""
Tests for data models in src/models/signage_data.py
"""

from datetime import datetime
from pathlib import Path

import pytest

from src.models.signage_data import (
    AmbientWeatherData,
    FerryData,
    PowerwallData,
    SignageContent,
    SpeedtestData,
    SportsData,
    StockData,
    TeslaData,
    WeatherData,
)


class TestSignageContent:
    """Test SignageContent base model."""

    def test_create_basic_content(self):
        """Test creating basic signage content."""
        content = SignageContent(
            lines=["Line 1", "Line 2"],
            filename_prefix="test",
        )

        assert content.lines == ["Line 1", "Line 2"]
        assert content.filename_prefix == "test"
        assert content.layout_type == "centered"  # default
        assert content.background_mode == "gradient"  # default

    def test_create_with_custom_layout(self):
        """Test creating content with custom layout."""
        content = SignageContent(
            lines=["Weather data"],
            filename_prefix="weather",
            layout_type="modern_weather",
            background_mode="local",
            background_query="weather/sunny",
        )

        assert content.layout_type == "modern_weather"
        assert content.background_mode == "local"
        assert content.background_query == "weather/sunny"

    def test_generate_filename(self):
        """Test filename generation with date."""
        content = SignageContent(
            lines=["Test"],
            filename_prefix="weather",
        )

        test_date = datetime(2025, 11, 28, 15, 30)
        filename = content.generate_filename(test_date)

        assert filename == "weather_2025-11-28.jpg"

    def test_with_map_image(self):
        """Test content with map image path."""
        map_path = Path("/tmp/ferry_map.png")
        content = SignageContent(
            lines=["Ferry schedule"],
            filename_prefix="ferry",
            map_image=map_path,
        )

        assert content.map_image == map_path


class TestWeatherData:
    """Test WeatherData model."""

    def test_create_weather_data(self):
        """Test creating weather data."""
        weather = WeatherData(
            city="Seattle",
            temperature=72.5,
            description="Clear sky",
            condition="sunny",
            feels_like=70.0,
            temp_high=75.0,
            temp_low=65.0,
            humidity=65,
            wind_speed=8.5,
            wind_direction=180,
        )

        assert weather.city == "Seattle"
        assert weather.temperature == 72.5
        assert weather.feels_like == 70.0
        assert weather.condition == "sunny"
        assert weather.humidity == 65

    def test_weather_to_signage(self):
        """Test converting weather data to signage content."""
        weather = WeatherData(
            city="Seattle",
            temperature=72.5,
            description="Clear sky",
            condition="sunny",
            feels_like=70.0,
            temp_high=75.0,
            temp_low=65.0,
            humidity=65,
            wind_speed=8.5,
            wind_direction=180,
        )

        signage = weather.to_signage()

        assert signage.filename_prefix == "weather"
        assert signage.layout_type == "modern_weather"
        assert signage.background_mode == "local"


class TestTeslaData:
    """Test TeslaData model."""

    def test_create_tesla_data(self):
        """Test creating Tesla vehicle data."""
        tesla = TeslaData(
            vehicle_name="Model Y",
            battery_level="86",
            range="222",
            charging_state="Disconnected",
            charge_limit_soc=90,
            climate_on=True,
            inside_temp=68.5,
            outside_temp=55.2,
            locked=True,
            odometer=12543.2,
        )

        assert tesla.vehicle_name == "Model Y"
        assert tesla.battery_level == "86"
        assert tesla.range == "222"
        assert tesla.climate_on
        assert tesla.locked

    def test_tesla_to_signage(self):
        """Test converting Tesla data to signage content."""
        tesla = TeslaData(
            vehicle_name="Model Y",
            battery_level="86",
            range="222",
        )

        signage = tesla.to_signage()

        assert signage.filename_prefix == "tesla"
        assert signage.layout_type == "modern_tesla"
        assert signage.background_mode == "local"


class TestPowerwallData:
    """Test PowerwallData model."""

    def test_create_powerwall_data(self):
        """Test creating Powerwall data."""
        powerwall = PowerwallData(
            site_name="Home",
            battery_percent=75.0,
            grid_status="Active",
            solar_power=5.2,
            home_power=3.1,
            battery_power=-2.1,  # charging
            backup_reserve_percent=20.0,
            storm_mode_active=False,
            site_status="online",
            grid_import=0.0,
            grid_export=0.0,
        )

        assert powerwall.site_name == "Home"
        assert powerwall.battery_percent == 75.0
        assert powerwall.battery_power == -2.1  # negative = charging

    def test_powerwall_to_signage(self):
        """Test converting Powerwall data to signage content."""
        powerwall = PowerwallData(
            site_name="Home",
            battery_percent=75.0,
            grid_status="Active",
            solar_power=5.2,
            home_power=3.1,
            battery_power=-2.1,
            backup_reserve_percent=20.0,
            storm_mode_active=False,
            site_status="online",
            grid_import=0.0,
            grid_export=0.0,
        )

        signage = powerwall.to_signage()

        assert signage.filename_prefix == "powerwall"
        assert signage.layout_type == "modern_powerwall"


class TestStockData:
    """Test StockData model."""

    def test_create_stock_data(self):
        """Test creating stock quote data."""
        stock = StockData(
            symbol="MSFT",
            price="380.50",
            change_percent="+0.73%",
        )

        assert stock.symbol == "MSFT"
        assert stock.price == "380.50"
        assert stock.change_percent == "+0.73%"

    def test_stock_to_signage(self):
        """Test converting stock data to signage content."""
        stock = StockData(
            symbol="MSFT",
            price="380.50",
            change_percent="+0.73%",
        )

        signage = stock.to_signage()

        assert signage.filename_prefix == "stock"
        assert signage.layout_type == "modern_stock"


class TestSpeedtestData:
    """Test SpeedtestData model."""

    def test_create_speedtest_data(self):
        """Test creating speedtest data."""
        speedtest = SpeedtestData(
            download=450.5,
            upload=25.3,
            ping=12.5,
            server_name="Test Server",
            server_host="speedtest.example.com",
            timestamp="2025-11-28 15:30:00",
        )

        assert speedtest.download == 450.5
        assert speedtest.upload == 25.3
        assert speedtest.ping == 12.5

    def test_speedtest_to_signage(self):
        """Test converting speedtest data to signage content."""
        speedtest = SpeedtestData(
            download=450.5,
            upload=25.3,
            ping=12.5,
            server_name="Test Server",
            server_host="speedtest.example.com",
            timestamp="2025-11-28 15:30:00",
        )

        signage = speedtest.to_signage()

        assert signage.filename_prefix == "speedtest"
        assert signage.layout_type == "modern_speedtest"


class TestFerryData:
    """Test FerryData model."""

    def test_create_ferry_data(self):
        """Test creating ferry schedule data."""
        ferry = FerryData(
            route="Fauntleroy-Southworth",
            status="normal",
        )

        assert ferry.route == "Fauntleroy-Southworth"
        assert ferry.status == "normal"
        assert ferry.delay_minutes == 0

    def test_ferry_to_signage(self):
        """Test converting ferry data to signage content."""
        ferry = FerryData(
            route="Fauntleroy-Southworth",
            status="normal",
        )

        signage = ferry.to_signage()

        assert signage.filename_prefix == "ferry"
        assert signage.layout_type == "modern_ferry"


class TestAmbientWeatherData:
    """Test AmbientWeatherData model."""

    def test_create_ambient_weather_data(self):
        """Test creating ambient weather station data."""
        ambient = AmbientWeatherData(
            station_name="Test Station",
            tempf=65.5,
            humidity=72,
            windspeedmph=8.5,
            winddir=180,
            baromrelin=29.92,
            feels_like=63.0,
            dew_point=55.0,
            dailyrainin=0.0,
            hourlyrainin=0.0,
            uv=3,
            solarradiation=450.0,
        )

        assert ambient.tempf == 65.5
        assert ambient.humidity == 72
        assert ambient.uv == 3
        assert ambient.solarradiation == 450.0

    def test_ambient_to_signage(self):
        """Test converting ambient weather data to signage content."""
        ambient = AmbientWeatherData(
            station_name="Test Station",
            tempf=65.5,
            humidity=72,
            windspeedmph=8.5,
            winddir=180,
            baromrelin=29.92,
            feels_like=63.0,
            dew_point=55.0,
            dailyrainin=0.0,
            hourlyrainin=0.0,
        )

        signage = ambient.to_signage()

        assert signage.filename_prefix == "ambient"
        assert signage.layout_type == "modern_ambient"


class TestSportsData:
    """Test SportsData model."""

    def test_create_sports_data(self):
        """Test creating sports fixture/standings data."""
        sports = SportsData(
            team_name="Arsenal",
            sport="football",
        )

        assert sports.team_name == "Arsenal"
        assert sports.sport == "football"

    def test_sports_to_signage(self):
        """Test converting sports data to signage content."""
        sports = SportsData(
            team_name="Arsenal",
            sport="football",
        )

        signage = sports.to_signage()

        assert signage.filename_prefix == "football_arsenal"
        assert signage.layout_type == "modern_football"
