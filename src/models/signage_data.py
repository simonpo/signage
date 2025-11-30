"""
Data models for signage content.
All data classes follow a clean pattern: fetch → model → SignageContent → render.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal


@dataclass
class SignageContent:
    """
    Base signage content model.
    This is what gets passed to the renderer.
    """

    lines: list[str]
    filename_prefix: str
    layout_type: Literal[
        "centered",
        "left",
        "grid",
        "split",
        "map",
        "weather",
        "modern_weather",
        "modern_stock",
        "modern_ambient",
        "modern_ferry",
        "modern_speedtest",
        "modern_sensors",
        "modern_football",
        "modern_rugby",
        "modern_tesla",
        "modern_powerwall",
        "modern_system",
    ] = "centered"
    background_mode: str = "gradient"
    background_query: str | None = None
    timestamp: datetime | None = None
    map_image: Path | None = None  # For ferry map composite
    metadata: dict = field(default_factory=dict)  # For carrying data objects to templates

    def generate_filename(self, date: datetime) -> str:
        """Generate date-based filename: prefix_YYYY-MM-DD.jpg"""
        date_str = date.strftime("%Y-%m-%d")
        return f"{self.filename_prefix}_{date_str}.jpg"


@dataclass
class PowerwallData:
    """Tesla Powerwall and energy site data from Fleet API."""

    site_name: str
    battery_percent: float
    grid_status: str
    solar_power: float  # kW
    home_power: float  # kW
    battery_power: float  # kW (positive=discharging, negative=charging)
    backup_reserve_percent: float
    storm_mode_active: bool
    site_status: str
    grid_import: float  # kW
    grid_export: float  # kW
    time_to_full: str | None = None
    time_to_empty: str | None = None
    alerts: list[str] = field(default_factory=list)

    def to_signage(self) -> SignageContent:
        """Convert to signage content with modern Powerwall layout."""
        return SignageContent(
            lines=[],  # Use custom HTML template
            filename_prefix="powerwall",
            layout_type="modern_powerwall",
            background_mode="local",
            background_query="tesla/powerwall",
        )


@dataclass
class TeslaVehicleData:
    """
    Base signage content model.
    This is what gets passed to the renderer.
    """

    lines: list[str]
    filename_prefix: str
    layout_type: Literal[
        "centered",
        "left",
        "grid",
        "split",
        "map",
        "weather",
        "modern_weather",
        "modern_stock",
        "modern_ambient",
        "modern_ferry",
        "modern_speedtest",
        "modern_sensors",
        "modern_football",
        "modern_rugby",
        "modern_tesla",
    ] = "centered"
    background_mode: str = "gradient"
    background_query: str | None = None
    timestamp: datetime | None = None
    map_image: Path | None = None  # For ferry map composite

    def generate_filename(self, date: datetime) -> str:
        """Generate date-based filename: prefix_YYYY-MM-DD.jpg"""
        date_str = date.strftime("%Y-%m-%d")
        return f"{self.filename_prefix}_{date_str}.jpg"


@dataclass
class TeslaData:
    """Tesla vehicle data from Fleet API."""

    vehicle_name: str = "Tesla"
    battery_level: str = ""
    battery_unit: str = "%"
    range: str = ""
    range_unit: str = " mi"
    charging_state: str = ""
    charge_limit_soc: int = 0
    time_to_full: str = ""
    charger_power: float = 0.0
    plugged_in: bool = False
    odometer: float = 0.0
    inside_temp: float = 0.0
    outside_temp: float = 0.0
    climate_on: bool = False
    defrost_on: bool = False
    software_version: str = ""
    locked: bool = False
    sentry_mode: bool = False
    latitude: float = 0.0
    longitude: float = 0.0
    heading: int = 0
    shift_state: str = ""
    speed: float = 0.0
    tire_pressure: dict = field(default_factory=dict)
    last_seen: str = ""
    online: bool = True
    location_display: str = ""
    cached_at: str | None = None  # ISO timestamp when data was cached

    def to_signage(self) -> SignageContent:
        """Convert to signage content with modern HTML layout."""
        from dataclasses import asdict
        return SignageContent(
            lines=[],  # Empty - using modern HTML template
            filename_prefix="tesla",
            layout_type="modern_tesla",
            background_mode="local",
            background_query="tesla/modelY",
            metadata={"tesla_data": self},
        )


@dataclass
class WeatherData:
    """Weather information from OpenWeatherMap."""

    city: str
    temperature: float
    description: str
    condition: Literal[
        "sunny", "rainy", "cloudy", "foggy", "snowy", "windy", "thunderstorm", "default"
    ]
    feels_like: float
    temp_high: float
    temp_low: float
    humidity: int
    wind_speed: float
    wind_direction: int
    visibility: int | None = None  # meters
    cloudiness: int | None = None  # percentage 0-100
    pressure: int | None = None  # hPa
    sunrise: int | None = None  # unix timestamp
    sunset: int | None = None  # unix timestamp
    wind_gust: float | None = None  # mph
    rain_1h: float | None = None  # mm in last hour

    def to_signage(self) -> SignageContent:
        """Convert to signage with beautiful multi-section layout."""
        lines = []

        # Title with city
        lines.append(self.city.upper())
        lines.append("")

        # Main temperature - large and centered
        lines.append(f"{self.temperature:.0f}°F")
        lines.append(self.description.title())
        lines.append("")

        # Two-column layout for details
        # Left column: Temperature details
        left_col = [
            f"High: {self.temp_high:.0f}°",
            f"Low: {self.temp_low:.0f}°",
            f"Feels: {self.feels_like:.0f}°",
        ]

        # Right column: Conditions
        wind_dir = self._wind_direction_to_compass(self.wind_direction)
        visibility_mi = self.visibility / 1609.34 if self.visibility else None

        right_col = [
            f"Humidity: {self.humidity}%",
            f"Wind: {self.wind_speed:.0f} mph {wind_dir}",
        ]

        if visibility_mi is not None and visibility_mi < 6:  # Only show if reduced visibility
            right_col.append(f"Visibility: {visibility_mi:.1f} mi")

        # Combine columns
        max_rows = max(len(left_col), len(right_col))
        for i in range(max_rows):
            left = left_col[i] if i < len(left_col) else ""
            right = right_col[i] if i < len(right_col) else ""
            lines.append(f"{left:<20}   {right}")

        return SignageContent(
            lines=lines,
            filename_prefix="weather",
            layout_type="modern_weather",
            background_mode="local",
            background_query=f"weather/{self.condition}",
            metadata={"weather_data": self},
        )

    def _wind_direction_to_compass(self, degrees: int) -> str:
        """Convert wind direction degrees to compass direction."""
        if degrees is None:
            return ""

        directions = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]
        index = round(degrees / 22.5) % 16
        return directions[index]


@dataclass
class AmbientWeatherData:
    """Hyper-local weather from personal Ambient Weather station."""

    station_name: str
    tempf: float
    humidity: int
    windspeedmph: float
    winddir: int
    baromrelin: float
    feels_like: float
    dew_point: float
    dailyrainin: float
    hourlyrainin: float
    temp_high: float | None = None
    temp_low: float | None = None
    solarradiation: float | None = None
    uv: int | None = None
    # Indoor air quality
    pm25_in: float | None = None  # Indoor PM2.5 µg/m³
    aqi_pm25_in: int | None = None  # AQI from PM2.5
    co2_in: int | None = None  # Indoor CO2 ppm
    tempinf: float | None = None  # Indoor temperature
    humidityin: int | None = None  # Indoor humidity

    def to_signage(self) -> SignageContent:
        """Convert to signage with modern card layout."""
        # Determine weather condition for background
        if self.hourlyrainin > 0:
            condition = "rainy"
        elif self.dailyrainin > 0:
            condition = "cloudy"
        elif self.solarradiation is not None and self.solarradiation == 0:
            # Nighttime (no solar radiation) - use default/night background
            condition = "default"
        else:
            condition = "sunny"

        return SignageContent(
            lines=[],  # Empty - we'll use custom card renderer
            filename_prefix="ambient",
            layout_type="modern_ambient",  # Modern dashboard layout
            background_mode="local",
            background_query=f"weather/{condition}",
            metadata={"weather_data": self},
        )

    def _aqi_quality(self, aqi: int) -> str:
        """Convert AQI value to quality description."""
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Moderate"
        elif aqi <= 150:
            return "Unhealthy for Sensitive"
        elif aqi <= 200:
            return "Unhealthy"
        elif aqi <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"

    def _co2_quality(self, co2: int) -> str:
        """Convert CO2 ppm to quality description."""
        if co2 < 400:
            return "Outdoor Level"
        elif co2 < 1000:
            return "Good"
        elif co2 < 2000:
            return "Acceptable"
        elif co2 < 5000:
            return "Poor"
        else:
            return "Very Poor"

    def _wind_direction_to_compass(self, degrees: int) -> str:
        """Convert wind direction degrees to compass direction."""
        if degrees is None:
            return ""

        directions = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSW",
            "SW",
            "WSW",
            "W",
            "WNW",
            "NW",
            "NNW",
        ]
        index = round(degrees / 22.5) % 16
        return directions[index]


@dataclass
class SpeedtestData:
    """Internet speed test results."""

    download: float  # Mbps
    upload: float  # Mbps
    ping: float  # ms
    server_name: str
    server_host: str
    timestamp: str
    url: str | None = None

    def to_signage(self) -> SignageContent:
        """Convert to signage with modern HTML layout."""
        lines = [
            "INTERNET SPEED",
            "",
            f"↓ {self.download:.1f} Mbps",
            f"↑ {self.upload:.1f} Mbps",
            f"⚡ {self.ping:.1f} ms",
            "",
            f"Server: {self.server_name}",
            f"{self.server_host}",
            "",
            f"Tested: {self.timestamp}",
        ]

        return SignageContent(
            lines=lines,
            filename_prefix="speedtest",
            layout_type="modern_speedtest",
            background_mode="local",
            background_query="speedtest",
        )


@dataclass
class AmbientSensorData:
    """Individual sensor reading from Ambient Weather station."""

    name: str
    temperature: float | None = None
    humidity: int | None = None
    battery_ok: bool | None = None


@dataclass
class AmbientMultiSensorData:
    """Collection of all sensors from Ambient Weather station."""

    station_name: str
    outdoor_temp: float
    outdoor_humidity: int
    sensors: list[AmbientSensorData] = field(default_factory=list)
    last_updated: str | None = None

    def to_signage(self) -> SignageContent:
        """Convert to signage with compact grid layout showing all sensors."""
        lines = []

        # Title
        lines.append(f"{self.station_name.upper()} - SENSORS")
        lines.append("")

        # Main outdoor conditions
        lines.append(f"Outdoor: {self.outdoor_temp:.1f}°F  {self.outdoor_humidity}%")
        lines.append("")

        # Sensor readings in compact format
        if self.sensors:
            lines.append("SENSOR          TEMP      HUMIDITY")
            lines.append("─" * 50)

            for sensor in self.sensors:
                # Format sensor name (truncate if needed)
                name = sensor.name[:14].ljust(14)

                # Format temperature
                if sensor.temperature is not None:
                    temp_str = f"{sensor.temperature:5.1f}°F"
                else:
                    temp_str = "  ---  "

                # Format humidity
                hum_str = f"{sensor.humidity:3d}%" if sensor.humidity is not None else " -- "

                # Battery indicator
                batt_icon = "" if sensor.battery_ok else " ⚠"

                lines.append(f"{name}  {temp_str}    {hum_str}{batt_icon}")
        else:
            lines.append("No additional sensors found")

        # Timestamp if available
        if self.last_updated:
            lines.append("")
            lines.append(f"Updated: {self.last_updated}")

        return SignageContent(
            lines=lines,
            filename_prefix="sensors",
            layout_type="modern_sensors",
            background_mode="local",
            background_query="sensors",
            metadata={"sensors_data": self},
        )


@dataclass
class StockData:
    """Stock quote from Alpha Vantage."""

    symbol: str
    price: str
    change_percent: str

    def to_signage(self) -> SignageContent:
        """Convert to signage content with symbol and price."""
        return SignageContent(
            lines=[
                self.symbol,
                f"${self.price}",
                self.change_percent,
            ],
            filename_prefix="stock",
            layout_type="modern_stock",
            background_mode="local",
            background_query="stock",
            metadata={"stock_data": self},
        )


@dataclass
class SportsFixture:
    """Upcoming sports match/game."""

    date: str
    home_team: str
    away_team: str
    competition: str
    venue: str = ""
    is_home_game: bool = False


@dataclass
class SportsResult:
    """Completed sports match result."""

    date: str
    home_team: str
    away_team: str
    home_score: str
    away_score: str
    competition: str


@dataclass
class LeagueTableRow:
    """League/standings table row."""

    position: int
    team: str
    played: int
    won: int
    drawn: int
    lost: int
    points: int
    goal_difference: int = 0


@dataclass
class SportsData:
    """
    Sports team information with fixtures, results, and standings.
    Designed for left-aligned layout with team branding.
    """

    team_name: str
    sport: Literal["nfl", "football", "rugby", "cricket"]
    last_result: SportsResult | None = None
    next_fixtures: list[SportsFixture] = field(default_factory=list)
    league_table: list[LeagueTableRow] = field(default_factory=list)
    is_live: bool = False
    live_score: str | None = None
    team_logo_url: str | None = None
    primary_color: str = "#003366"
    secondary_color: str = "#69BE28"
    league_name: str = "Standings"

    def to_signage(self) -> SignageContent:
        """Convert to signage with left-aligned layout and team colors."""
        lines = [self.team_name]

        # Live score gets priority
        if self.is_live and self.live_score:
            lines.append("🔴 LIVE")
            lines.append(self.live_score)

        # Last result
        if self.last_result:
            result = self.last_result
            lines.append("")
            lines.append("Last Match")
            lines.append(
                f"{result.home_team} {result.home_score} - "
                f"{result.away_score} {result.away_team}"
            )

        # Next fixtures
        if self.next_fixtures:
            lines.append("")
            lines.append("Upcoming")
            for fixture in self.next_fixtures[:3]:
                match_line = f"{fixture.home_team} vs {fixture.away_team}"
                lines.append(f"{fixture.date} - {match_line}")

        # League position (top 5)
        if self.league_table:
            lines.append("")
            lines.append("Standings")
            for row in self.league_table[:5]:
                lines.append(
                    f"{row.position}. {row.team} - {row.points}pts " f"({row.played}P {row.won}W)"
                )

        # Create background query with fallback hierarchy:
        # 1. Team-specific: sports/{sport}/{team_slug}
        # 2. Generic sport: sports/{sport}/generic
        # 3. Gradient (handled by BackgroundFactory if both return None)
        team_slug = self.team_name.lower().replace(" ", "_").replace(".", "")
        background_query = f"sports/{self.sport}/{team_slug}|sports/{self.sport}/generic"

        return SignageContent(
            lines=lines,
            filename_prefix=f"{self.sport}_{team_slug}",
            layout_type=f"modern_{self.sport}",
            background_mode="local",
            background_query=background_query,
            metadata={"sports_data": self},
        )


@dataclass
class FerrySchedule:
    """Ferry departure schedule."""

    departure_time: str
    arrival_time: str
    vessel_name: str
    departing_terminal: str


@dataclass
class FerryVessel:
    """Real-time ferry vessel position."""

    name: str
    latitude: float
    longitude: float
    speed: float
    heading: float


@dataclass
class FerryData:
    """
    Ferry route information with schedule, vessels, and alerts.
    Uses split layout: text on left, map on right.
    """

    route: str
    status: Literal["normal", "delayed", "cancelled"]
    delay_minutes: int = 0
    southworth_departures: list[FerrySchedule] = field(default_factory=list)
    fauntleroy_departures: list[FerrySchedule] = field(default_factory=list)
    vessels: list[FerryVessel] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)
    wait_time_minutes: int | None = None

    def to_signage(self, map_path: Path | None = None) -> SignageContent:
        """
        Convert to signage with grid layout.
        Two columns: Southworth departures | Fauntleroy departures
        """
        lines = []

        # Title and status on first row
        if self.status == "cancelled":
            status_text = "SERVICE CANCELLED"
        elif self.status == "delayed":
            status_text = f"DELAYED {self.delay_minutes} min"
        else:
            status_text = "On Time"

        lines.append(f"{self.route} - {status_text}")

        # Two-column layout: build both columns to same length
        left_col = ["FROM SOUTHWORTH"]
        right_col = ["FROM FAUNTLEROY"]

        # Southworth departures (left column)
        if self.southworth_departures:
            for dep in self.southworth_departures[:7]:
                left_col.append(f"{dep.departure_time}")
                left_col.append(f"  {dep.vessel_name}")
        else:
            left_col.append("No departures")

        # Fauntleroy departures (right column)
        if self.fauntleroy_departures:
            for dep in self.fauntleroy_departures[:7]:
                right_col.append(f"{dep.departure_time}")
                right_col.append(f"  {dep.vessel_name}")
        else:
            right_col.append("No departures")

        # Combine columns with spacing
        max_rows = max(len(left_col), len(right_col))
        for i in range(max_rows):
            left = left_col[i] if i < len(left_col) else ""
            right = right_col[i] if i < len(right_col) else ""
            lines.append(f"{left:<45} {right}")

        # Alerts at bottom if present
        if self.alerts:
            lines.append("")
            lines.append("ALERTS: " + self.alerts[0][:60])

        return SignageContent(
            lines=lines,
            filename_prefix="ferry",
            layout_type="modern_ferry",  # Modern HTML schedule layout
            background_mode="local",
            background_query="ferry",
            map_image=map_path,
            metadata={"ferry_data": self},
        )


@dataclass
class FerryMapData:
    """Ferry vessel positions for full-screen map view."""

    vessels: list[FerryVessel] = field(default_factory=list)
    timestamp: str | None = None

    def to_signage(self) -> SignageContent:
        """Convert to signage - map rendered separately, no text overlay."""
        return SignageContent(
            lines=[],  # No text, pure map
            filename_prefix="ferry_map",
            layout_type="map",
            background_mode="none",
            background_query="",
        )


@dataclass
class SystemHealthData:
    """System health and observability metrics."""

    status: str  # "healthy", "degraded", "down"
    uptime: str
    generators: dict[str, dict]  # {source: {success, failure, last_run}}
    recent_errors: list[dict]  # [{timestamp, level, message}]
    disk_space: dict[str, float]  # {total_gb, used_gb, free_gb, percent_used}
    images_generated: dict[str, int]  # {source: count, total: count}
    log_file_size: dict[str, str | float]  # {size_mb, size_formatted}

    def to_signage(self) -> SignageContent:
        """Convert to signage content for system health display."""
        return SignageContent(
            lines=[],  # Use HTML template
            filename_prefix="system",
            layout_type="modern_system",
            background_mode="gradient",
            background_query="system/health",
            metadata={"system_data": self},
        )
