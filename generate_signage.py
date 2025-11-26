#!/usr/bin/env python3
"""
Generate signage images for Samsung Frame TV.
Modular architecture with clean separation of concerns.
"""

import argparse
import logging
import sys

from src.clients.ambient_weather import AmbientWeatherClient
from src.clients.ferry import FerryClient
from src.clients.homeassistant import HomeAssistantClient
from src.clients.marine_traffic import MarineTrafficClient
from src.clients.speedtest import SpeedtestClient
from src.clients.sports.nfl import NFLClient
from src.clients.stock import StockClient
from src.clients.weather import WeatherClient
from src.clients.whale_tracker import WhaleTrackerClient
from src.config import Config
from src.models.signage_data import TeslaData
from src.renderers.image_renderer import SignageRenderer
from src.renderers.map_renderer import MapRenderer
from src.utils.file_manager import FileManager
from src.utils.logging_utils import setup_logging
from src.utils.output_manager import OutputManager

# === LOGGING ===
# Use new logging setup from utils
setup_logging()
logger = logging.getLogger(__name__)


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


def generate_tesla(
    renderer: SignageRenderer, ha_client: HomeAssistantClient, file_mgr: FileManager
) -> None:
    """Generate Tesla signage."""
    try:
        logger.info("Generating Tesla signage...")

        # Fetch data from Home Assistant
        batt, battr = ha_client.get_entity_state(Config.TESLA_BATTERY)
        rng, rattr = ha_client.get_entity_state(Config.TESLA_RANGE)

        # Create data model
        tesla_data = TeslaData(
            battery_level=batt,
            battery_unit=battr.get("unit_of_measurement", "%"),
            range=rng,
            range_unit=rattr.get("unit_of_measurement", " mi"),
        )

        # Convert to signage content
        content = tesla_data.to_signage()

        # Render
        _render_and_save(renderer, content, "tesla")

        # Cleanup old files
        file_mgr.cleanup_old_files("tesla")

        logger.info("✓ Tesla signage complete")

    except Exception as e:
        logger.error(f"Failed to generate Tesla signage: {e}")


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

        logger.info("✓ Weather signage complete")

    except Exception as e:
        logger.error(f"Failed to generate weather signage: {e}")


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

        logger.info(f"✓ Speedtest signage complete: {speedtest_data.download:.1f} Mbps down")

    except Exception as e:
        logger.error(f"Failed to generate speedtest signage: {e}")


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

        logger.info("✓ Stock signage complete")

    except Exception as e:
        logger.error(f"Failed to generate stock signage: {e}")


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

        logger.info("✓ Ferry signage complete")

    except Exception as e:
        logger.error(f"Failed to generate ferry signage: {e}")


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
        timestamp = Config.get_current_time()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"ferry_map_{timestamp_str}.png"

        paths = output_manager.save_image(ferry_map_img, filename, source="ferry_map")

        # Cleanup old files
        file_mgr.cleanup_old_files("ferry_map")

        logger.info(f"✓ Ferry map complete: {len(paths)} profile(s)")
        logger.info(f"  Vessels: {len(ferry_map_data.vessels)}")

    except Exception as e:
        logger.error(f"Failed to generate ferry map: {e}")
        raise


def generate_whales(
    renderer: SignageRenderer, whale_client: WhaleTrackerClient, file_mgr: FileManager
) -> None:
    """Generate whale sighting signage."""
    try:
        logger.info("Generating whale sightings signage...")

        # Fetch whale data
        whale_data = whale_client.get_sightings()

        if not whale_data:
            logger.warning("No whale data available")
            return

        # Convert to signage content
        content = whale_data.to_signage()

        # Render
        _render_and_save(renderer, content, "whales")

        # Cleanup
        file_mgr.cleanup_old_files("whales")

        logger.info("✓ Whale signage complete")

    except Exception as e:
        logger.error(f"Failed to generate whale signage: {e}")


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


def generate_marine(
    marine_client: MarineTrafficClient, output_manager: OutputManager, file_mgr: FileManager
) -> None:
    """Generate marine traffic signage via screenshot."""
    try:
        logger.info("Generating marine traffic signage...")

        # Capture marine traffic map
        marine_data = marine_client.capture_map()

        if not marine_data or not marine_data.screenshot_path:
            logger.warning("No marine traffic data available")
            return

        # Load screenshot and save via OutputManager
        from PIL import Image

        marine_img = Image.open(marine_data.screenshot_path)

        timestamp = Config.get_current_time()
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        filename = f"marine_{timestamp_str}.png"

        paths = output_manager.save_image(marine_img, filename, source="marine")

        # Cleanup old files
        file_mgr.cleanup_old_files("marine")

        logger.info(f"✓ Marine traffic complete: {len(paths)} profile(s)")
        logger.info(f"   Timestamp: {timestamp.strftime('%I:%M %p')}")

    except Exception as e:
        logger.error(f"Failed to generate marine traffic signage: {e}")


# === MAIN ===


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate signage images for Samsung Frame TV")
    parser.add_argument(
        "--source",
        choices=[
            "all",
            "tesla",
            "weather",
            "ambient",
            "sensors",
            "speedtest",
            "stock",
            "ferry",
            "ferry_map",
            "marine",
            "whales",
            "sports",
            "nfl",
            "arsenal",
            "football",
            "rugby",
        ],
        default="all",
        help="Which signage to generate",
    )
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode with scheduler")
    parser.add_argument("--html", action="store_true", help="Use HTML rendering instead of PIL")

    args = parser.parse_args()

    # Validate configuration
    try:
        Config.validate()
    except RuntimeError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    # Initialize output manager and renderer
    output_manager = OutputManager()
    renderer = SignageRenderer(use_html=args.html, output_manager=output_manager)
    file_mgr = FileManager()

    logger.info(f"Rendering mode: {'HTML' if args.html else 'PIL (legacy)'}")

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
            with HomeAssistantClient() as ha_client:
                generate_tesla(renderer, ha_client, file_mgr)

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

        if args.source in ["all", "whales"]:
            with WhaleTrackerClient() as whale_client:
                generate_whales(renderer, whale_client, file_mgr)

        if args.source in ["all", "marine"]:
            marine_client = MarineTrafficClient()
            generate_marine(marine_client, output_manager, file_mgr)

        if args.source in ["all", "sports", "nfl"]:
            generate_sports(renderer, file_mgr, sport_type=args.source)

        if args.source in ["arsenal", "football"]:
            generate_sports(renderer, file_mgr, sport_type="arsenal")

        if args.source == "rugby":
            generate_sports(renderer, file_mgr, sport_type="rugby")

        logger.info(f"All signage generation complete. Files in: {Config.OUTPUT_PATH}")


if __name__ == "__main__":
    main()
