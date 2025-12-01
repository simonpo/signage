"""
HTML template renderer using Jinja2.
Provides utilities for rendering HTML templates to images via headless browser.
"""

import logging
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.config import Config

logger = logging.getLogger(__name__)


class TemplateRenderer:
    """
    Renders Jinja2 HTML templates with context data.
    Templates are located in src/templates/ directory.
    """

    def render_powerwall_display(self, powerwall_data: Any) -> str:
        """
        Render modern Powerwall display.

        Args:
            powerwall_data: PowerwallData object

        Returns:
            Rendered HTML string
        """
        context = {
            "site_name": powerwall_data.site_name,
            "battery_percent": powerwall_data.battery_percent,
            "grid_status": powerwall_data.grid_status,
            "solar_power": powerwall_data.solar_power,
            "home_power": powerwall_data.home_power,
            "battery_power": powerwall_data.battery_power,
            "backup_reserve_percent": powerwall_data.backup_reserve_percent,
            "storm_mode_active": powerwall_data.storm_mode_active,
            "site_status": powerwall_data.site_status,
            "grid_import": powerwall_data.grid_import,
            "grid_export": powerwall_data.grid_export,
            "time_to_full": powerwall_data.time_to_full,
            "time_to_empty": powerwall_data.time_to_empty,
            "alerts": powerwall_data.alerts,
        }
        return self.render("modern_powerwall_layout.html", context)

    def __init__(self, templates_dir: Path | None = None):
        """
        Initialize template renderer.

        Args:
            templates_dir: Path to templates directory (defaults to src/templates)
        """
        if templates_dir is None:
            templates_dir = Config.BASE_DIR / "src" / "templates"

        self.templates_dir = templates_dir

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

        # Add custom filters
        self._register_filters()

        logger.debug(f"TemplateRenderer initialized with templates from {templates_dir}")

    def _register_filters(self):
        """Register custom Jinja2 filters."""

        def do_enumerate(iterable, start=0):
            """Enumerate filter for Jinja2."""
            return enumerate(iterable, start)

        def wind_direction_compass(degrees):
            """Convert wind direction degrees to compass direction."""
            if degrees is None:
                return "N"

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

        # Register filters
        self.env.filters["enumerate"] = do_enumerate
        self.env.filters["compass"] = wind_direction_compass

    def render(self, template_name: str, context: dict[str, Any]) -> str:
        """
        Render template with context data.

        Args:
            template_name: Name of template file (e.g., "centered_layout.html")
            context: Dictionary of context variables for template

        Returns:
            Rendered HTML string

        Raises:
            TemplateNotFound: If template file doesn't exist
            TemplateSyntaxError: If template has syntax errors
        """
        try:
            template = self.env.get_template(template_name)
            html = template.render(**context)

            logger.debug(f"Rendered template: {template_name}")
            return html

        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}", exc_info=True)
            raise

    def render_layout(self, layout_type: str, lines: list, **kwargs) -> str:
        """
        Render a text layout template.

        Args:
            layout_type: Layout type (centered, left, grid, split, weather)
            lines: List of text lines to render
            **kwargs: Additional context variables

        Returns:
            Rendered HTML string
        """
        template_name = f"{layout_type}_layout.html"
        context = {"lines": lines, **kwargs}

        return self.render(template_name, context)

    def render_weather_cards(self, weather_data: Any) -> str:
        """
        Render weather cards template.

        Args:
            weather_data: AmbientWeatherData object

        Returns:
            Rendered HTML string
        """
        # Calculate wind direction compass
        wind_direction = self._wind_direction_to_compass(weather_data.winddir)

        context = {"weather": weather_data, "wind_direction": wind_direction}

        return self.render("weather_cards.html", context)

    def render_ambient_dashboard(self, weather_data: Any) -> str:
        """
        Render modern ambient weather dashboard.

        Args:
            weather_data: AmbientWeatherData object

        Returns:
            Rendered HTML string
        """
        context = {
            "station_name": weather_data.station_name,
            "tempf": weather_data.tempf,
            "humidity": weather_data.humidity,
            "windspeedmph": weather_data.windspeedmph,
            "winddir": weather_data.winddir,
            "dailyrainin": weather_data.dailyrainin,
            "uv": weather_data.uv,
            "solarradiation": weather_data.solarradiation,
            "baromrelin": weather_data.baromrelin,
            "feels_like": weather_data.feels_like,
            "dew_point": weather_data.dew_point,
            "hourlyrainin": weather_data.hourlyrainin,
            "temp_high": weather_data.temp_high,
            "temp_low": weather_data.temp_low,
            "tempinf": weather_data.tempinf,
            "humidityin": weather_data.humidityin,
            "pm25_in": weather_data.pm25_in,
            "aqi_pm25_in": weather_data.aqi_pm25_in,
            "co2_in": weather_data.co2_in,
        }

        return self.render("modern_ambient_layout.html", context)

    def render_ferry_schedule(self, ferry_data: Any) -> str:
        """
        Render modern ferry schedule.

        Args:
            ferry_data: FerryData object

        Returns:
            Rendered HTML string
        """
        context = {
            "route": ferry_data.route,
            "status": ferry_data.status,
            "delay_minutes": ferry_data.delay_minutes,
            "southworth_departures": ferry_data.southworth_departures,
            "fauntleroy_departures": ferry_data.fauntleroy_departures,
            "alerts": ferry_data.alerts,
            "wait_time_minutes": ferry_data.wait_time_minutes,
        }

        return self.render("modern_ferry_layout.html", context)

    def render_stock_quote(self, stock_data: Any) -> str:
        """
        Render modern stock quote.

        Args:
            stock_data: StockData object

        Returns:
            Rendered HTML string
        """
        # Parse change percent to determine positive/negative
        change_str = stock_data.change_percent
        is_positive = not change_str.startswith("-")

        context = {
            "symbol": stock_data.symbol,
            "price": stock_data.price,
            "change_percent": stock_data.change_percent,
            "is_positive": is_positive,
        }

        return self.render("modern_stock_layout.html", context)

    def render_speedtest_results(self, speedtest_data: Any) -> str:
        """
        Render modern speedtest results.

        Args:
            speedtest_data: SpeedtestData object

        Returns:
            Rendered HTML string
        """
        context = {
            "download_mbps": speedtest_data.download,
            "upload_mbps": speedtest_data.upload,
            "ping_ms": speedtest_data.ping,
            "jitter_ms": 0,  # Not available in current data
            "server_location": speedtest_data.server_name,
        }

        return self.render("modern_speedtest_layout.html", context)

    def render_sensors_display(self, sensors_data: Any) -> str:
        """
        Render modern sensors display.

        Args:
            sensors_data: AmbientMultiSensorData object

        Returns:
            Rendered HTML string
        """
        from datetime import datetime

        # Find greenhouse and chickens sensors
        greenhouse_temp = None
        greenhouse_humidity = None
        chickens_temp = None
        chickens_humidity = None

        for sensor in sensors_data.sensors:
            if sensor.name == "Greenhouse":
                greenhouse_temp = sensor.temperature
                greenhouse_humidity = sensor.humidity
            elif sensor.name == "Chickens":
                chickens_temp = sensor.temperature
                chickens_humidity = sensor.humidity

        # Format current time
        now = datetime.now()
        formatted_datetime = now.strftime("%B %d, %Y at %I:%M %p").replace(" 0", " ")

        context = {
            "date_time": formatted_datetime,
            "outdoor_temp": sensors_data.outdoor_temp,
            "outdoor_humidity": sensors_data.outdoor_humidity,
            "greenhouse_temp": greenhouse_temp,
            "greenhouse_humidity": greenhouse_humidity,
            "chickens_temp": chickens_temp,
            "chickens_humidity": chickens_humidity,
        }

        return self.render("modern_sensors_layout.html", context)

    def render_football_display(self, sports_data: Any) -> str:
        """
        Render modern football (soccer) display.

        Args:
            sports_data: SportsData object

        Returns:
            Rendered HTML string
        """
        context = {
            "team_name": sports_data.team_name,
            "is_live": sports_data.is_live,
            "live_score": sports_data.live_score,
            "last_result": sports_data.last_result,
            "next_fixtures": sports_data.next_fixtures,
            "league_table": sports_data.league_table,
            "league_name": sports_data.league_name,
        }

        return self.render("modern_football_layout.html", context)

    def render_rugby_display(self, sports_data: Any) -> str:
        """
        Render modern rugby display.

        Args:
            sports_data: SportsData object

        Returns:
            Rendered HTML string
        """
        context = {
            "team_name": sports_data.team_name,
            "is_live": sports_data.is_live,
            "live_score": sports_data.live_score,
            "last_result": sports_data.last_result,
            "next_fixtures": sports_data.next_fixtures,
        }

        return self.render("modern_rugby_layout.html", context)

    def render_weather_display(self, weather_data: Any) -> str:
        """
        Render modern weather display with comprehensive information.

        Args:
            weather_data: WeatherData object

        Returns:
            Rendered HTML string
        """
        from datetime import datetime

        # Format sunrise/sunset times if available
        sunrise_time = None
        sunset_time = None
        if weather_data.sunrise:
            sunrise_time = (
                datetime.fromtimestamp(weather_data.sunrise).strftime("%I:%M %p").lstrip("0")
            )
        if weather_data.sunset:
            sunset_time = (
                datetime.fromtimestamp(weather_data.sunset).strftime("%I:%M %p").lstrip("0")
            )

        # Convert visibility to miles
        visibility_mi = None
        if weather_data.visibility:
            visibility_mi = weather_data.visibility / 1609.34

        # Convert rain from mm to inches
        rain_in = None
        if weather_data.rain_1h:
            rain_in = weather_data.rain_1h / 25.4

        # Determine if it's day or night based on sunrise/sunset
        is_daytime = True
        if weather_data.sunrise and weather_data.sunset:
            import time

            current_time = time.time()
            is_daytime = weather_data.sunrise <= current_time <= weather_data.sunset

        # Format current timestamp
        current_timestamp = datetime.now().strftime("%A, %B %d at %I:%M %p").replace(" 0", " ")

        context = {
            "city": weather_data.city,
            "temperature": weather_data.temperature,
            "description": weather_data.description,
            "condition": weather_data.condition,
            "feels_like": weather_data.feels_like,
            "temp_high": weather_data.temp_high,
            "temp_low": weather_data.temp_low,
            "humidity": weather_data.humidity,
            "wind_speed": weather_data.wind_speed,
            "wind_direction": weather_data.wind_direction,
            "wind_gust": weather_data.wind_gust,
            "visibility_mi": visibility_mi,
            "cloudiness": weather_data.cloudiness,
            "pressure": weather_data.pressure,
            "sunrise_time": sunrise_time,
            "sunset_time": sunset_time,
            "rain_in": rain_in,
            "is_daytime": is_daytime,
            "timestamp": current_timestamp,
        }

        return self.render("modern_weather_layout.html", context)

    def render_tesla_display(self, tesla_data: Any) -> str:
        """
        Render modern Tesla vehicle display.

        Args:
            tesla_data: TeslaData object

        Returns:
            Rendered HTML string
        """
        from datetime import datetime

        # Format cached_at timestamp if present
        cached_at_display = None
        if tesla_data.cached_at:
            try:
                cached_dt = datetime.fromisoformat(tesla_data.cached_at)
                cached_at_display = cached_dt.strftime("%B %d, %Y at %I:%M %p")
            except Exception:
                cached_at_display = tesla_data.cached_at

        context = {
            "vehicle_name": tesla_data.vehicle_name,
            "vehicle_type": tesla_data.vehicle_type,
            "last_updated": tesla_data.last_updated,
            "battery_level": tesla_data.battery_level,
            "battery_unit": tesla_data.battery_unit,
            "range": tesla_data.range,
            "range_unit": tesla_data.range_unit,
            "charging_state": tesla_data.charging_state,
            "charge_limit_soc": tesla_data.charge_limit_soc,
            "time_to_full": tesla_data.time_to_full,
            "charger_power": tesla_data.charger_power,
            "plugged_in": tesla_data.plugged_in,
            "odometer": tesla_data.odometer,
            "inside_temp": tesla_data.inside_temp,
            "outside_temp": tesla_data.outside_temp,
            "climate_on": tesla_data.climate_on,
            "defrost_on": tesla_data.defrost_on,
            "software_version": tesla_data.software_version,
            "locked": tesla_data.locked,
            "sentry_mode": tesla_data.sentry_mode,
            "latitude": tesla_data.latitude,
            "longitude": tesla_data.longitude,
            "heading": tesla_data.heading,
            "shift_state": tesla_data.shift_state,
            "speed": tesla_data.speed,
            "tire_pressure": tesla_data.tire_pressure,
            "last_seen": tesla_data.last_seen,
            "online": tesla_data.online,
            "location_display": tesla_data.location_display,
            "cached_at": cached_at_display,
        }

        return self.render("modern_tesla_layout.html", context)

    def _wind_direction_to_compass(self, degrees: int | None) -> str:
        """Convert wind direction degrees to compass direction."""
        if degrees is None:
            return "N"

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

    def render_system_health(self, system_data) -> str:
        """
        Render system health dashboard.

        Args:
            system_data: SystemHealthData object or dict with system health metrics

        Returns:
            Rendered HTML string
        """
        # Convert dataclass to dict if needed
        from dataclasses import asdict, is_dataclass

        if is_dataclass(system_data):
            context = asdict(system_data)  # type: ignore[arg-type]  # Runtime check ensures it's a dataclass
        elif isinstance(system_data, dict):
            context = system_data
        else:
            raise ValueError(f"Expected dict or dataclass, got {type(system_data)}")

        # Flatten nested dicts for template compatibility
        if "disk_space" in context and isinstance(context["disk_space"], dict):
            disk = context.pop("disk_space")
            context["disk_total_gb"] = disk.get("total_gb", 0)
            context["disk_used_gb"] = disk.get("used_gb", 0)
            context["disk_free_gb"] = disk.get("free_gb", 0)
            context["disk_percent_used"] = disk.get("percent_used", 0)

        if "log_file_size" in context and isinstance(context["log_file_size"], dict):
            log_size = context.pop("log_file_size")
            context["log_size_mb"] = log_size.get("size_mb", 0)
            context["log_size_formatted"] = log_size.get("size_formatted", "0 MB")

        if "images_generated" in context and isinstance(context["images_generated"], dict):
            images = context.pop("images_generated")
            context["total_images"] = images.get("total", 0)
            context["images_by_source"] = {k: v for k, v in images.items() if k != "total"}

        # Add error_count from recent_errors
        context["error_count"] = len(context.get("recent_errors", []))

        return self.render("modern_system_layout.html", context)

    def save_html(self, html: str, output_path: Path) -> None:
        """
        Save rendered HTML to file.

        Args:
            html: Rendered HTML string
            output_path: Path to save HTML file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"Saved HTML to {output_path}")
