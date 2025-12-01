#!/usr/bin/env python3
"""
Generate signage images for Samsung Frame TV.
Modular architecture with clean separation of concerns.
"""

import argparse
import logging

from src.clients.ambient_weather import AmbientWeatherClient
from src.clients.ferry import FerryClient
from src.clients.speedtest import SpeedtestClient
from src.clients.sports.nfl import NFLClient
from src.clients.stock import StockClient
from src.clients.system_health import SystemHealthClient
from src.clients.tesla_fleet import TeslaFleetClient
from src.clients.weather import WeatherClient
from src.config import Config
from src.models.signage_data import PowerwallData, SystemHealthData, TeslaData
from src.renderers.image_renderer import SignageRenderer
from src.renderers.map_renderer import MapRenderer
from src.utils.file_manager import FileManager
from src.utils.logging_utils import setup_logging, timeit
from src.utils.output_manager import OutputManager

# === LOGGING ===
# Use new logging setup from utils
setup_logging()
logger = logging.getLogger(__name__)


# === GENERATOR FUNCTIONS ===


@timeit
def generate_powerwall(
    renderer: SignageRenderer, tesla_client: TeslaFleetClient, file_mgr: FileManager
) -> None:
    """Generate Powerwall signage."""
    try:
        logger.info("Generating Powerwall signage...")

        # Get energy sites (Powerwalls, solar, etc.)
        sites = tesla_client.get_energy_sites()
        if not sites or len(sites) == 0:
            logger.warning("No energy sites found")
            return

        # Use first site (most users have one)
        site = sites[0]
        site_id = str(site["id"])
        site_name = site.get("site_name", "Powerwall")

        logger.info(f"Fetching data for {site_name} (ID: {site_id})")

        # Get live status
        data = tesla_client.get_energy_site_data(site_id)
        if not data:
            logger.warning("Failed to fetch Powerwall data")
            return

        # Extract fields
        battery_percent = data.get("percentage_charged", 0.0)
        grid_status = data.get("grid_status", "Unknown")
        solar_power = data.get("solar_power", 0.0)
        home_power = data.get("load_power", 0.0)
        battery_power = data.get("battery_power", 0.0)
        backup_reserve_percent = data.get("backup_reserve_percent", 0.0)
        storm_mode_active = data.get("storm_mode_active", False)
        site_status = data.get("site_status", "Unknown")
        grid_import = data.get("grid_import", 0.0)
        grid_export = data.get("grid_export", 0.0)
        time_to_full = data.get("time_to_full_charge")
        time_to_empty = data.get("time_to_empty")
        alerts = data.get("alerts", [])

        # Create data model
        powerwall_data = PowerwallData(
            site_name=site_name,
            battery_percent=battery_percent,
            grid_status=grid_status,
            solar_power=solar_power,
            home_power=home_power,
            battery_power=battery_power,
            backup_reserve_percent=backup_reserve_percent,
            storm_mode_active=storm_mode_active,
            site_status=site_status,
            grid_import=grid_import,
            grid_export=grid_export,
            time_to_full=time_to_full,
            time_to_empty=time_to_empty,
            alerts=alerts,
        )

        # Convert to signage content
        content = powerwall_data.to_signage()

        # Render with simple filename
        timestamp = Config.get_current_time()
        filename = "powerwall.png"
        renderer.render(
            content, filename=filename, timestamp=timestamp, powerwall_data=powerwall_data
        )

        logger.info(f"✓ Powerwall signage complete - {battery_percent:.0f}% battery, {grid_status}")

    except Exception as e:
        logger.error(f"✗ Powerwall signage failed: {e}")


# === GENERATOR FUNCTIONS ===


def _render_and_save(
    renderer: SignageRenderer, content, filename_prefix: str, timestamp=None
) -> None:
    """
    Helper to render content and handle multi-resolution output.

    Args:
        renderer: SignageRenderer instance
        content: SignageContent object
        filename_prefix: Base filename
        timestamp: Optional timestamp
    """
    if timestamp is None:
        timestamp = Config.get_current_time()

    timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp_str}.png"

    # Render to all output profiles
    paths = renderer.render(content, filename=filename, timestamp=timestamp)

    logger.info(f"✓ Saved to {len(paths)} output profile(s)")
    for path in paths:
        logger.debug(f"  - {path}")


@timeit
def generate_tesla(
    renderer: SignageRenderer, tesla_client: TeslaFleetClient, file_mgr: FileManager
) -> None:

    try:
        logger.info("Generating Tesla signage...")

        # Get vehicles from Fleet API
        vehicles = tesla_client.get_vehicles()
        if not vehicles or len(vehicles) == 0:
            logger.warning("No vehicles found")
            return

        # Use first vehicle (most users have one)
        vehicle = vehicles[0]
        vehicle_id = vehicle["id"]
        vehicle_name = vehicle.get("display_name", "Tesla")
        logger.debug(f"Using vehicle: {vehicle_name} (ID: {vehicle_id})")

        # Get vehicle data
        vehicle_data = tesla_client.get_vehicle_data(str(vehicle_id))
        cached_data = None
        using_cache = False

        if not vehicle_data:
            # Try to use cached data as fallback
            cached_data = tesla_client.get_cached_vehicle_data(str(vehicle_id))
            if cached_data:
                vehicle_data = cached_data["data"]
                using_cache = True
                cached_at = cached_data["cached_at"]
                logger.info(f"Using cached vehicle data from {cached_at} (vehicle is asleep)")
            else:
                logger.warning(
                    "Vehicle data unavailable and no cache - vehicle may be asleep or out of connectivity"
                )
                return

        # Extract all relevant fields
        charge_state = vehicle_data.get("charge_state", {})
        climate_state = vehicle_data.get("climate_state", {})
        vehicle_state = vehicle_data.get("vehicle_state", {})
        drive_state = vehicle_data.get("drive_state", {})
        tire_pressure = vehicle_data.get("vehicle_config", {}).get("tpms_pressure", {})

        battery_level = charge_state.get("battery_level")
        battery_range = charge_state.get("battery_range")
        charging_state = charge_state.get("charging_state", "")
        charge_limit_soc = charge_state.get("charge_limit_soc", 0)
        time_to_full = charge_state.get("time_to_full_charge", "")
        charger_power = charge_state.get("charger_power", 0.0)
        conn_charge_cable = charge_state.get("conn_charge_cable", "")

        # Improved plugged_in and charging logic
        plugged_in = conn_charge_cable not in (None, "", "Disconnected")
        is_charging = charging_state.lower() in ("charging", "starting") or (
            charger_power and charger_power > 0
        )

        odometer = vehicle_state.get("odometer", 0.0)
        inside_temp = climate_state.get("inside_temp", 0.0)
        outside_temp = climate_state.get("outside_temp", 0.0)
        climate_on = climate_state.get("is_climate_on", False)
        defrost_on = climate_state.get("defrost_mode", 0) == 1
        software_version = vehicle_state.get("software_version", "")
        locked = vehicle_state.get("locked", False)
        sentry_mode = vehicle_state.get("sentry_mode", False)
        latitude = drive_state.get("latitude", 0.0)
        longitude = drive_state.get("longitude", 0.0)
        heading = drive_state.get("heading", 0)
        shift_state = drive_state.get("shift_state", "")
        speed = drive_state.get("speed", 0.0)
        # Tire pressure: not always available, so fallback to empty dict
        tire_pressure = vehicle_state.get("tpms_pressure", {}) or {}
        last_seen = vehicle.get("last_seen", "")
        online = vehicle.get("state", "online") == "online"
        location_display = drive_state.get("native_location", "") or ""

        tesla_data = TeslaData(
            vehicle_name=vehicle_name,
            battery_level=str(battery_level) if battery_level is not None else "",
            battery_unit="%",
            range=str(int(battery_range)) if battery_range is not None else "",
            range_unit=" mi",
            charging_state=charging_state,
            charge_limit_soc=charge_limit_soc,
            time_to_full=str(time_to_full) if time_to_full is not None else "",
            charger_power=charger_power,
            plugged_in=plugged_in,
            odometer=odometer,
            inside_temp=inside_temp,
            outside_temp=outside_temp,
            climate_on=climate_on,
            defrost_on=defrost_on,
            software_version=software_version,
            locked=locked,
            sentry_mode=sentry_mode,
            latitude=latitude,
            longitude=longitude,
            heading=heading,
            shift_state=shift_state,
            speed=speed,
            tire_pressure=tire_pressure,
            last_seen=last_seen,
            online=online,
            location_display=location_display,
            cached_at=cached_data["cached_at"] if using_cache else None,
        )

        # Convert to signage content
        content = tesla_data.to_signage()

        # Render with simple filename
        timestamp = Config.get_current_time()
        filename = "tesla.png"
        renderer.render(content, filename=filename, timestamp=timestamp, tesla_data=tesla_data)

        # Success message with key metrics
        charge_status = "charging" if is_charging else "idle"
        logger.info(
            f"✓ Tesla signage complete - {battery_level}% battery, {int(battery_range)}mi range ({charge_status})"
        )

    except Exception as e:
        logger.error(f"✗ Tesla signage failed: {e}")


@timeit
def generate_weather(
    renderer: SignageRenderer, weather_client: WeatherClient, file_mgr: FileManager
) -> None:
    """Generate weather signage."""
    try:
        logger.info("Generating weather signage...")

        # Fetch weather data
        weather_data = weather_client.get_weather()

        if not weather_data:
            logger.warning("No weather data available")
            return

        # Convert to signage content
        content = weather_data.to_signage()

        # Render with simple filename
        timestamp = Config.get_current_time()
        filename = "weather.png"
        renderer.render(content, filename=filename, timestamp=timestamp, weather_data=weather_data)

        # No cleanup - always overwrite same file

        logger.info(
            f"✓ Weather signage complete - {weather_data.temperature}°F, {weather_data.description}"
        )

    except Exception as e:
        logger.error(f"✗ Weather signage failed: {e}")


def generate_ambient_weather(
    renderer: SignageRenderer, ambient_client: AmbientWeatherClient, file_mgr: FileManager
) -> None:
    """Generate Ambient Weather station signage."""
    try:
        logger.info("Generating Ambient Weather signage...")

        # Fetch data from personal weather station
        ambient_data = ambient_client.get_weather()

        if not ambient_data:
            logger.warning("No Ambient Weather data available")
            return

        # Convert to signage content
        content = ambient_data.to_signage()

        # Get timestamp
        timestamp = Config.get_current_time()
        filename = "ambient.png"

        # Render with weather data for card-based layout
        renderer.render(content, filename=filename, timestamp=timestamp, weather_data=ambient_data)

        # No cleanup - always overwrite same file

        logger.info("✓ Ambient Weather signage complete")

    except Exception as e:
        logger.error(f"Failed to generate Ambient Weather signage: {e}")


def generate_ambient_sensors(
    renderer: SignageRenderer, ambient_client: AmbientWeatherClient, file_mgr: FileManager
) -> None:
    """Generate multi-sensor display showing all Ambient Weather sensors."""
    try:
        logger.info("Generating Ambient Weather multi-sensor display...")

        # Fetch all sensor data
        sensor_data = ambient_client.get_all_sensors()

        if not sensor_data:
            logger.warning("No Ambient Weather sensor data available")
            return

        logger.info(
            f"Ambient Sensors: Outdoor {sensor_data.outdoor_temp:.1f}°F, {len(sensor_data.sensors)} additional sensors"
        )

        # Convert to signage content
        content = sensor_data.to_signage()

        # Render with simple filename
        timestamp = Config.get_current_time()
        filename = "sensors.png"
        renderer.render(content, filename=filename, timestamp=timestamp, sensors_data=sensor_data)

        # No cleanup - always overwrite same file

        logger.info(f"✓ Multi-sensor display complete ({len(sensor_data.sensors)} sensors)")

    except Exception as e:
        logger.error(f"Failed to generate multi-sensor display: {e}")


@timeit
def generate_speedtest(
    renderer: SignageRenderer, speedtest_client: SpeedtestClient, file_mgr: FileManager
) -> None:
    """Generate speedtest signage."""
    try:
        logger.info("Generating speedtest signage...")

        # Fetch latest speedtest data
        speedtest_data = speedtest_client.get_latest()

        if not speedtest_data:
            logger.warning("No speedtest data available")
            return

        # Convert to signage content
        content = speedtest_data.to_signage()

        # Render with simple filename
        timestamp = Config.get_current_time()
        filename = "speedtest.png"
        renderer.render(
            content, filename=filename, timestamp=timestamp, speedtest_data=speedtest_data
        )

        # No cleanup - always overwrite same file

        logger.info(
            f"✓ Speedtest signage complete - {speedtest_data.download:.0f}↓ {speedtest_data.upload:.0f}↑ Mbps"
        )

    except Exception as e:
        logger.error(f"✗ Speedtest signage failed: {e}")


@timeit
def generate_stock(
    renderer: SignageRenderer, stock_client: StockClient, file_mgr: FileManager
) -> None:
    """Generate stock quote signage."""
    try:
        logger.info("Generating stock signage...")

        # Fetch stock data
        stock_data = stock_client.get_quote()

        if not stock_data:
            logger.warning("No stock data available")
            return

        # Convert to signage content
        content = stock_data.to_signage()

        # Render with simple filename
        timestamp = Config.get_current_time()
        filename = "stock.png"
        renderer.render(content, filename=filename, timestamp=timestamp, stock_data=stock_data)

        # No cleanup - always overwrite same file

        logger.info(f"✓ Stock signage complete - {stock_data.symbol} ${stock_data.price}")

    except Exception as e:
        logger.error(f"✗ Stock signage failed: {e}")


@timeit
def generate_ferry(
    renderer: SignageRenderer, ferry_client: FerryClient, file_mgr: FileManager
) -> None:
    """Generate ferry schedule signage."""
    try:
        logger.info("Generating ferry signage...")

        # Fetch ferry data
        ferry_data = ferry_client.get_ferry_data()

        if not ferry_data:
            logger.warning("No ferry data available")
            return

        # Render ferry map if we have vessel data
        map_path = None
        if ferry_data.vessels:
            map_renderer = MapRenderer()
            ferry_map = map_renderer.render_ferry_map(ferry_data.vessels)

            # Save map temporarily
            map_path = Config.CACHE_PATH / "ferry_map_temp.jpg"
            ferry_map.save(map_path, "JPEG", quality=95)

        # Convert to signage content
        content = ferry_data.to_signage(map_path)

        # Get timestamp
        timestamp = Config.get_current_time()
        filename = "ferry.png"

        # Render with ferry data for modern HTML layout
        renderer.render(content, filename=filename, timestamp=timestamp, ferry_data=ferry_data)

        # No cleanup - always overwrite same file

        departures_count = len(ferry_data.southworth_departures) + len(
            ferry_data.fauntleroy_departures
        )
        logger.info(f"✓ Ferry signage complete - {departures_count} departures")

    except Exception as e:
        logger.error(f"✗ Ferry signage failed: {e}")


def generate_ferry_map(
    ferry_client: FerryClient, output_manager: OutputManager, file_mgr: FileManager
) -> None:
    """Generate full-screen ferry map with all vessel positions."""
    try:
        from src.renderers.ferry_map_renderer import FerryMapRenderer

        logger.info("Generating ferry map...")

        # Fetch all vessel locations
        ferry_map_data = ferry_client.get_all_vessel_locations()

        if not ferry_map_data or not ferry_map_data.vessels:
            logger.warning("No ferry vessel data available for map")
            return

        # Render full-screen map
        map_renderer = FerryMapRenderer()
        ferry_map_img = map_renderer.render_full_map(ferry_map_data.vessels)

        # Save using OutputManager
        filename = "ferry_map.png"

        paths = output_manager.save_image(ferry_map_img, filename, source="ferry_map")

        # Cleanup old files
        file_mgr.cleanup_old_files("ferry_map")

        logger.info(f"✓ Ferry map complete: {len(paths)} profile(s)")
        logger.info(f"  Vessels: {len(ferry_map_data.vessels)}")

    except Exception as e:
        logger.error(f"Failed to generate ferry map: {e}")
        raise


@timeit
def generate_system(renderer: SignageRenderer, file_mgr: FileManager) -> None:
    """Generate system health signage."""
    try:
        logger.info("Generating system health signage...")

        # Collect system health data
        health_client = SystemHealthClient()
        health_data = health_client.get_health_data()

        if not health_data:
            logger.warning("No system health data available")
            return

        # Calculate status
        generators = health_data.get("generators", {})
        total_failures = sum(g.get("failure", 0) for g in generators.values())
        total_runs = sum(g.get("success", 0) + g.get("failure", 0) for g in generators.values())
        success_rate = (total_runs - total_failures) / total_runs * 100 if total_runs > 0 else 100

        if success_rate >= 95:
            status = "HEALTHY"
        elif success_rate >= 80:
            status = "DEGRADED"
        else:
            status = "DOWN"

        # Format time_ago for each generator
        from datetime import datetime

        now = datetime.now()
        for _name, stats in generators.items():
            if stats.get("last_run"):
                delta = now - stats["last_run"]
                if delta.total_seconds() < 60:
                    stats["time_ago"] = f"{int(delta.total_seconds())}s ago"
                elif delta.total_seconds() < 3600:
                    stats["time_ago"] = f"{int(delta.total_seconds() / 60)}m ago"
                else:
                    stats["time_ago"] = f"{int(delta.total_seconds() / 3600)}h ago"
            else:
                stats["time_ago"] = "never"

        # Create data model
        system_data = SystemHealthData(
            status=status,
            uptime=health_data["uptime"]["formatted"],
            generators=generators,
            recent_errors=health_data.get("recent_errors", []),
            disk_space=health_data.get("disk_space", {}),
            images_generated=health_data.get("images_generated", {}),
            log_file_size=health_data.get("log_file_size", {}),
        )

        # Convert to signage content
        content = system_data.to_signage()

        # Prepare template variables
        timestamp = Config.get_current_time()
        filename = "system.png"

        # Render with system data
        template_vars = {
            "status": status,
            "uptime": system_data.uptime,
            "generators": system_data.generators,
            "disk_free_gb": system_data.disk_space.get("free_gb", 0),
            "total_images": system_data.images_generated.get("total", 0),
            "log_size": system_data.log_file_size.get("size_formatted", "0 KB"),
            "error_count": len(system_data.recent_errors),
        }

        renderer.render(content, filename=filename, timestamp=timestamp, system_data=template_vars)

        logger.info(
            f"✓ System health signage complete - {status}, {success_rate:.0f}% success rate"
        )

    except Exception as e:
        logger.error(f"✗ System health signage failed: {e}")


def generate_sports(
    renderer: SignageRenderer, file_mgr: FileManager, sport_type: str = "all"
) -> None:
    """Generate sports signage for enabled teams."""
    try:
        logger.info(f"Generating sports signage ({sport_type})...")

        generated = 0

        # NFL / Seahawks
        if (sport_type in ["all", "nfl"]) and Config.SEAHAWKS_ENABLED:
            try:
                nfl_client = NFLClient()
                sports_data = nfl_client.get_team_data()

                if sports_data:
                    content = sports_data.to_signage()
                    _render_and_save(renderer, content, "nfl_seahawks")
                    file_mgr.cleanup_old_files("nfl_seahawks")
                    generated += 1

            except Exception as e:
                logger.error(f"Failed to generate NFL signage: {e}")

        # Arsenal (Football)
        if (sport_type in ["all", "football", "arsenal"]) and Config.ARSENAL_ENABLED:
            try:
                from src.clients.sports.football import FootballClient

                football_client = FootballClient()
                sports_data = football_client.get_team_data(Config.ARSENAL_TEAM_ID)

                if sports_data:
                    content = sports_data.to_signage()
                    timestamp = Config.get_current_time()
                    filename = "arsenal.png"
                    renderer.render(
                        content, filename=filename, timestamp=timestamp, sports_data=sports_data
                    )
                    generated += 1

            except Exception as e:
                logger.error(f"Failed to generate Arsenal signage: {e}")

        # England Rugby
        if (sport_type in ["all", "rugby"]) and Config.ENGLAND_RUGBY_ENABLED:
            try:
                from src.clients.sports.rugby import RugbyClient

                rugby_client = RugbyClient()
                sports_data = rugby_client.get_team_data()  # No team ID needed (mock data)

                if sports_data:
                    content = sports_data.to_signage()
                    timestamp = Config.get_current_time()
                    filename = "england_rugby.png"
                    renderer.render(
                        content, filename=filename, timestamp=timestamp, sports_data=sports_data
                    )
                    generated += 1

            except Exception as e:
                logger.error(f"Failed to generate England Rugby signage: {e}")

        # TODO: Add Cricket when implemented

        if generated > 0:
            logger.info(f"✓ Sports signage complete ({generated} generated)")
        else:
            logger.warning("No sports teams enabled")

    except Exception as e:
        logger.error(f"Failed to generate sports signage: {e}")


# === MAIN ===


def main():
    """Main entry point."""
    # Check for plugin system config (sources.yaml)

    from src.plugins.config.loader import ConfigLoader

    plugin_config = ConfigLoader.load()

    if plugin_config:
        # Use plugin system
        logger.info("Using plugin system (sources.yaml found)")
        # Import sources to register them
        import src.plugins.sources  # noqa: F401
        from src.plugins.executor import PluginExecutor

        executor = PluginExecutor(plugin_config)

        # Check if user wants to run specific source
        import sys

        if len(sys.argv) > 1 and "--source" in sys.argv:
            # Extract source ID from args
            source_idx = sys.argv.index("--source") + 1
            if source_idx < len(sys.argv):
                source_id = sys.argv[source_idx]
                logger.info(f"Running single source: {source_id}")
                executor.run(source_filter=source_id)
            else:
                executor.run()
        else:
            # Run all enabled sources
            executor.run()

        return

    # Otherwise use legacy CLI system
    logger.info("Using legacy CLI mode (sources.yaml not found)")

    parser = argparse.ArgumentParser(description="Generate signage images for Samsung Frame TV")
    parser.add_argument(
        "--source",
        choices=[
            "all",
            "tesla",
            "powerwall",
            "weather",
            "ambient",
            "sensors",
            "speedtest",
            "stock",
            "ferry",
            "ferry_map",
            "sports",
            "nfl",
            "arsenal",
            "football",
            "rugby",
            "system",
        ],
        default="all",
        help="Which signage to generate",
    )
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode with scheduler")
    parser.add_argument("--html", action="store_true", help="Use HTML rendering instead of PIL")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate images without uploading to TV (for testing)",
    )
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Generate sources.yaml from current .env configuration",
    )

    args = parser.parse_args()

    # Handle migration first
    if args.migrate:
        from dotenv import load_dotenv

        from src.plugins.migrator import ConfigMigrator

        load_dotenv()
        migrator = ConfigMigrator()
        migrator.write_config()
        return

    # Config is automatically validated on import via Pydantic
    # No need for explicit Config.validate() call

    # Initialize output manager and renderer
    output_manager = OutputManager()
    renderer = SignageRenderer(use_html=args.html, output_manager=output_manager)
    file_mgr = FileManager()

    logger.info(f"Rendering mode: {'HTML' if args.html else 'PIL (legacy)'}")

    if args.dry_run:
        logger.info("DRY RUN MODE: Images will be generated but NOT uploaded to TV")
        output_manager.dry_run = True

    # Run generators based on source selection
    if args.daemon:
        # Import and run scheduler
        from src.scheduler import SignageScheduler

        logger.info("Starting daemon mode...")
        scheduler = SignageScheduler(renderer, file_mgr)
        scheduler.run_daemon()

    else:
        # One-time generation
        if args.source in ["all", "tesla"]:
            with TeslaFleetClient() as tesla_client:
                generate_tesla(renderer, tesla_client, file_mgr)

        if args.source in ["all", "powerwall"]:
            with TeslaFleetClient() as tesla_client:
                generate_powerwall(renderer, tesla_client, file_mgr)

        if args.source in ["all", "weather"]:
            with WeatherClient() as weather_client:
                generate_weather(renderer, weather_client, file_mgr)

        if args.source == "ambient":
            with AmbientWeatherClient() as ambient_client:
                generate_ambient_weather(renderer, ambient_client, file_mgr)

        if args.source == "sensors":
            with AmbientWeatherClient() as ambient_client:
                generate_ambient_sensors(renderer, ambient_client, file_mgr)

        if args.source == "speedtest":
            with SpeedtestClient() as speedtest_client:
                generate_speedtest(renderer, speedtest_client, file_mgr)

        if args.source in ["all", "stock"]:
            with StockClient() as stock_client:
                generate_stock(renderer, stock_client, file_mgr)

        if args.source in ["all", "ferry"]:
            with FerryClient() as ferry_client:
                generate_ferry(renderer, ferry_client, file_mgr)

        if args.source == "ferry_map":
            with FerryClient() as ferry_client:
                generate_ferry_map(ferry_client, output_manager, file_mgr)

        if args.source in ["all", "sports", "nfl"]:
            generate_sports(renderer, file_mgr, sport_type=args.source)

        if args.source in ["arsenal", "football"]:
            generate_sports(renderer, file_mgr, sport_type="arsenal")

        if args.source == "rugby":
            generate_sports(renderer, file_mgr, sport_type="rugby")

        if args.source == "system":
            generate_system(renderer, file_mgr)

        logger.info(f"All signage generation complete. Files in: {Config.OUTPUT_PATH}")


if __name__ == "__main__":
    main()
