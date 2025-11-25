#!/usr/bin/env python3
"""
Generate signage images for Samsung Frame TV.
Modular architecture with clean separation of concerns.
"""

import argparse
import logging
import sys
from typing import Optional

from src.clients.ferry import FerryClient
from src.clients.homeassistant import HomeAssistantClient
from src.clients.marine_traffic import MarineTrafficClient
from src.clients.sports.nfl import NFLClient
from src.clients.stock import StockClient
from src.clients.weather import WeatherClient
from src.clients.ambient_weather import AmbientWeatherClient
from src.clients.speedtest import SpeedtestClient
from src.clients.whale_tracker import WhaleTrackerClient
from src.config import Config
from src.models.signage_data import TeslaData
from src.renderers.image_renderer import SignageRenderer
from src.renderers.map_renderer import MapRenderer
from src.utils.file_manager import FileManager

# === LOGGING ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


# === GENERATOR FUNCTIONS ===

def generate_tesla(
    renderer: SignageRenderer,
    ha_client: HomeAssistantClient,
    file_mgr: FileManager
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
            range_unit=rattr.get("unit_of_measurement", " mi")
        )
        
        # Convert to signage content
        content = tesla_data.to_signage()
        
        # Get output path and timestamp
        timestamp = Config.get_current_time()
        output_path = file_mgr.get_file_path("tesla", timestamp)
        
        # Render
        renderer.render(content, output_path, timestamp)
        
        # Cleanup old files
        file_mgr.cleanup_old_files("tesla")
        
        logger.info("✓ Tesla signage complete")
    
    except Exception as e:
        logger.error(f"Failed to generate Tesla signage: {e}")


def generate_weather(
    renderer: SignageRenderer,
    weather_client: WeatherClient,
    file_mgr: FileManager
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
        
        # Get output path and timestamp
        timestamp = Config.get_current_time()
        output_path = file_mgr.get_file_path("weather", timestamp)
        
        # Render
        renderer.render(content, output_path, timestamp)
        
        # Cleanup
        file_mgr.cleanup_old_files("weather")
        
        logger.info("✓ Weather signage complete")
    
    except Exception as e:
        logger.error(f"Failed to generate weather signage: {e}")


def generate_ambient_weather(
    renderer: SignageRenderer,
    ambient_client: AmbientWeatherClient,
    file_mgr: FileManager
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
        
        # Get output path and timestamp
        timestamp = Config.get_current_time()
        output_path = file_mgr.get_file_path("ambient", timestamp)
        
        # Render
        renderer.render(content, output_path, timestamp)
        
        # Cleanup
        file_mgr.cleanup_old_files("ambient")
        
        logger.info("✓ Ambient Weather signage complete")
    
    except Exception as e:
        logger.error(f"Failed to generate Ambient Weather signage: {e}")


def generate_ambient_sensors(
    renderer: SignageRenderer,
    ambient_client: AmbientWeatherClient,
    file_mgr: FileManager
) -> None:
    """Generate multi-sensor display showing all Ambient Weather sensors."""
    try:
        logger.info("Generating Ambient Weather multi-sensor display...")
        
        # Fetch all sensor data
        sensor_data = ambient_client.get_all_sensors()
        
        if not sensor_data:
            logger.warning("No Ambient Weather sensor data available")
            return
        
        # Convert to signage content
        content = sensor_data.to_signage()
        
        # Get output path and timestamp
        timestamp = Config.get_current_time()
        output_path = file_mgr.get_file_path("sensors", timestamp)
        
        # Render
        renderer.render(content, output_path, timestamp)
        
        # Cleanup
        file_mgr.cleanup_old_files("sensors")
        
        logger.info(f"✓ Multi-sensor display complete ({len(sensor_data.sensors)} sensors)")
    
    except Exception as e:
        logger.error(f"Failed to generate multi-sensor display: {e}")


def generate_speedtest(
    renderer: SignageRenderer,
    speedtest_client: SpeedtestClient,
    file_mgr: FileManager
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
        
        # Get output path and timestamp
        timestamp = Config.get_current_time()
        output_path = file_mgr.get_file_path("speedtest", timestamp)
        
        # Render
        renderer.render(content, output_path, timestamp)
        
        # Cleanup
        file_mgr.cleanup_old_files("speedtest")
        
        logger.info(f"✓ Speedtest signage complete: {speedtest_data.download:.1f} Mbps down")
    
    except Exception as e:
        logger.error(f"Failed to generate speedtest signage: {e}")


def generate_stock(
    renderer: SignageRenderer,
    stock_client: StockClient,
    file_mgr: FileManager
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
        
        # Get output path and timestamp
        timestamp = Config.get_current_time()
        output_path = file_mgr.get_file_path("stock", timestamp)
        
        # Render
        renderer.render(content, output_path, timestamp)
        
        # Cleanup
        file_mgr.cleanup_old_files("stock")
        
        logger.info("✓ Stock signage complete")
    
    except Exception as e:
        logger.error(f"Failed to generate stock signage: {e}")


def generate_ferry(
    renderer: SignageRenderer,
    ferry_client: FerryClient,
    file_mgr: FileManager
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
        
        # Get output path and timestamp
        timestamp = Config.get_current_time()
        output_path = file_mgr.get_file_path("ferry", timestamp)
        
        # Render (will composite map onto right half if map_path provided)
        renderer.render(content, output_path, timestamp)
        
        # Cleanup
        file_mgr.cleanup_old_files("ferry")
        
        logger.info("✓ Ferry signage complete")
    
    except Exception as e:
        logger.error(f"Failed to generate ferry signage: {e}")


def generate_whales(
    renderer: SignageRenderer,
    whale_client: WhaleTrackerClient,
    file_mgr: FileManager
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
        
        # Get output path and timestamp
        timestamp = Config.get_current_time()
        output_path = file_mgr.get_file_path("whales", timestamp)
        
        # Render
        renderer.render(content, output_path, timestamp)
        
        # Cleanup
        file_mgr.cleanup_old_files("whales")
        
        logger.info("✓ Whale signage complete")
    
    except Exception as e:
        logger.error(f"Failed to generate whale signage: {e}")


def generate_sports(
    renderer: SignageRenderer,
    file_mgr: FileManager,
    sport_type: str = "all"
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
                    timestamp = Config.get_current_time()
                    output_path = file_mgr.get_file_path("nfl_seahawks", timestamp)
                    
                    renderer.render(content, output_path, timestamp)
                    file_mgr.cleanup_old_files("nfl_seahawks")
                    generated += 1
            
            except Exception as e:
                logger.error(f"Failed to generate NFL signage: {e}")
        
        # TODO: Add Arsenal (football), Rugby, Cricket when implemented
        
        if generated > 0:
            logger.info(f"✓ Sports signage complete ({generated} generated)")
        else:
            logger.warning("No sports teams enabled")
    
    except Exception as e:
        logger.error(f"Failed to generate sports signage: {e}")


# === MAIN ===

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate signage images for Samsung Frame TV"
    )
    parser.add_argument(
        "--source",
        choices=["all", "tesla", "weather", "ambient", "sensors", "speedtest", "stock", "ferry", "whales", "sports", "nfl"],
        default="all",
        help="Which signage to generate"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run in daemon mode with scheduler"
    )
    
    args = parser.parse_args()
    
    # Validate configuration
    try:
        Config.validate()
    except RuntimeError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    
    # Initialize renderer and file manager
    renderer = SignageRenderer()
    file_mgr = FileManager()
    
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
        
        if args.source in ["all", "whales"]:
            with WhaleTrackerClient() as whale_client:
                generate_whales(renderer, whale_client, file_mgr)
        
        if args.source in ["all", "sports", "nfl"]:
            generate_sports(renderer, file_mgr, sport_type=args.source)
        
        logger.info(f"All signage generation complete. Files in: {Config.OUTPUT_PATH}")


if __name__ == "__main__":
    main()