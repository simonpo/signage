"""
Scheduler for daemon mode with live sports detection.
Manages update intervals and live event detection.
"""

import logging
import time
from datetime import datetime
from typing import Callable, Optional

from src.clients.ferry import FerryClient
from src.clients.homeassistant import HomeAssistantClient
from src.clients.sports.nfl import NFLClient
from src.clients.stock import StockClient
from src.clients.weather import WeatherClient
from src.config import Config
from src.renderers.image_renderer import SignageRenderer
from src.utils.file_manager import FileManager

logger = logging.getLogger(__name__)


class SignageScheduler:
    """
    Manages scheduled signage generation with live event detection.
    Adjusts update frequencies based on live sports events.
    """

    def __init__(self, renderer: SignageRenderer, file_mgr: FileManager):
        """
        Initialize scheduler.

        Args:
            renderer: SignageRenderer instance
            file_mgr: FileManager instance
        """
        self.renderer = renderer
        self.file_mgr = file_mgr
        self.last_run: dict[str, Optional[datetime]] = {}
        self.running = False

        # Default update intervals (in seconds)
        self.intervals = {
            "tesla": 900,  # 15 minutes
            "weather": 1800,  # 30 minutes
            "stock": 300,  # 5 minutes
            "ferry": 300,  # 5 minutes
            "whales": 3600,  # 1 hour
            "sports": 7200,  # 2 hours (when not live)
        }

        # Live event interval
        self.live_interval = Config.LIVE_UPDATE_INTERVAL  # 2 minutes default

    def register_generator(self, name: str, generator_func: Callable, interval: int) -> None:
        """
        Register a generator function with custom interval.

        Args:
            name: Generator name
            generator_func: Function to call
            interval: Update interval in seconds
        """
        self.generators[name] = generator_func
        self.intervals[name] = interval
        self.last_run[name] = None

        logger.debug(f"Registered generator '{name}' with {interval}s interval")

    def should_run(self, name: str) -> bool:
        """
        Check if generator should run now.

        Args:
            name: Generator name

        Returns:
            True if generator should run
        """
        # Never run before
        if self.last_run.get(name) is None:
            return True

        # Check if enough time has passed
        last = self.last_run[name]

        # Use live interval for sports if there's a live game
        interval = self.intervals[name]
        if name == "sports" and self._is_live_sports_event():
            interval = self.live_interval
            logger.debug("Live sports detected - using fast update interval")

        elapsed = (datetime.now() - last).total_seconds()
        return elapsed >= interval

    def _is_live_sports_event(self) -> bool:
        """
        Check if any sports team has a live game.

        Returns:
            True if live game detected
        """
        try:
            # Check NFL if enabled
            if Config.SEAHAWKS_ENABLED:
                nfl_client = NFLClient()
                if nfl_client.is_game_live():
                    return True

            # TODO: Check other sports when implemented
            # if Config.ARSENAL_ENABLED:
            #     football_client = FootballClient()
            #     if football_client.is_game_live():
            #         return True

        except Exception as e:
            logger.warning(f"Error checking live sports: {e}")

        return False

    def run_daemon(self) -> None:
        """
        Run scheduler in daemon mode.
        Continuously checks and runs generators.
        Press Ctrl+C to stop.
        """
        self.running = True
        logger.info("Scheduler started in daemon mode")
        logger.info(f"Update intervals: {self.intervals}")
        logger.info("Press Ctrl+C to stop")

        try:
            while self.running:
                # Check each generator
                self._check_and_run_tesla()
                self._check_and_run_weather()
                self._check_and_run_stock()
                self._check_and_run_ferry()
                self._check_and_run_whales()
                self._check_and_run_sports()

                # Sleep for 30 seconds before next check
                time.sleep(30)

        except KeyboardInterrupt:
            logger.info("\nReceived interrupt signal")
            self.stop()

    def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False
        logger.info("Scheduler stopped")

    def _check_and_run_tesla(self) -> None:
        """Check and run Tesla generator."""
        if not self.should_run("tesla"):
            return

        try:
            # Import here to avoid circular imports
            from generate_signage import generate_tesla

            with HomeAssistantClient() as ha_client:
                generate_tesla(self.renderer, ha_client, self.file_mgr)

            self.last_run["tesla"] = datetime.now()

        except Exception as e:
            logger.error(f"Tesla generator failed: {e}")

    def _check_and_run_weather(self) -> None:
        """Check and run weather generator."""
        if not self.should_run("weather"):
            return

        try:
            from generate_signage import generate_weather

            with WeatherClient() as weather_client:
                generate_weather(self.renderer, weather_client, self.file_mgr)

            self.last_run["weather"] = datetime.now()

        except Exception as e:
            logger.error(f"Weather generator failed: {e}")

    def _check_and_run_stock(self) -> None:
        """Check and run stock generator."""
        if not self.should_run("stock"):
            return

        try:
            from generate_signage import generate_stock

            with StockClient() as stock_client:
                generate_stock(self.renderer, stock_client, self.file_mgr)

            self.last_run["stock"] = datetime.now()

        except Exception as e:
            logger.error(f"Stock generator failed: {e}")

    def _check_and_run_ferry(self) -> None:
        """Check and run ferry generator."""
        if not self.should_run("ferry"):
            return

        try:
            from generate_signage import generate_ferry

            with FerryClient() as ferry_client:
                generate_ferry(self.renderer, ferry_client, self.file_mgr)

            self.last_run["ferry"] = datetime.now()

        except Exception as e:
            logger.error(f"Ferry generator failed: {e}")

    def _check_and_run_sports(self) -> None:
        """Check and run sports generators."""
        if not self.should_run("sports"):
            return

        try:
            from generate_signage import generate_sports

            generate_sports(self.renderer, self.file_mgr, sport_type="all")

            self.last_run["sports"] = datetime.now()

        except Exception as e:
            logger.error(f"Sports generator failed: {e}")
