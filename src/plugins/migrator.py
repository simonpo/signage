"""
Migration tool to generate sources.yaml from current .env configuration.
"""

import logging
import os
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class ConfigMigrator:
    """Generate sources.yaml from environment variables."""

    def migrate(self) -> dict:
        """
        Analyze current .env and generate sources.yaml structure.

        Returns:
            Dict ready to write as YAML
        """
        sources = []

        # Detect weather config
        if os.getenv("WEATHER_API_KEY"):
            sources.append(
                {
                    "id": "weather_default",
                    "type": "weather",
                    "enabled": True,
                    "schedule": "*/15 * * * *",
                    "config": {
                        "city": os.getenv("WEATHER_CITY", "Seattle"),
                        "api_key": "${WEATHER_API_KEY}",
                    },
                    "rendering": {
                        "layout": "modern_weather",
                        "background": os.getenv("WEATHER_BG_MODE", "local"),
                        "background_query": "weather/cloudy",
                    },
                }
            )

        # Detect Tesla config
        if os.getenv("TESLA_CLIENT_ID"):
            sources.append(
                {
                    "id": "tesla_default",
                    "type": "tesla",
                    "enabled": True,
                    "schedule": "*/30 * * * *",
                    "config": {"vehicle_index": 0},
                    "rendering": {
                        "layout": "tesla_card",
                        "background": "local",
                        "background_query": "tesla/model_y",
                    },
                }
            )

        # Detect Ferry config
        if os.getenv("FERRY_ROUTE"):
            sources.append(
                {
                    "id": "ferry_default",
                    "type": "ferry",
                    "enabled": True,
                    "schedule": "*/10 6-22 * * *",
                    "config": {},
                    "rendering": {
                        "layout": "ferry_map",
                        "background": "local",
                        "background_query": "ferry/puget_sound",
                    },
                }
            )

        # Detect Ambient Weather config
        if os.getenv("AMBIENT_API_KEY"):
            sources.append(
                {
                    "id": "ambient_weather_default",
                    "type": "ambient_weather",
                    "enabled": True,
                    "schedule": "*/15 * * * *",
                    "config": {},
                    "rendering": {
                        "layout": "default",
                        "background": "local",
                        "background_query": "weather/sunny",
                    },
                }
            )

            # Also add sensors display if sensor names are configured
            if os.getenv("AMBIENT_SENSOR_NAMES"):
                sources.append(
                    {
                        "id": "ambient_sensors_default",
                        "type": "ambient_sensors",
                        "enabled": True,
                        "schedule": "*/15 * * * *",
                        "config": {},
                        "rendering": {
                            "layout": "default",
                            "background": "gradient",
                        },
                    }
                )

        # Detect Speedtest config
        if os.getenv("SPEEDTEST_URL"):
            sources.append(
                {
                    "id": "speedtest_default",
                    "type": "speedtest",
                    "enabled": True,
                    "schedule": "0 */4 * * *",
                    "config": {},
                    "rendering": {
                        "layout": "default",
                        "background": "local",
                        "background_query": "speedtest/network",
                    },
                }
            )

        # Detect Stock config
        if os.getenv("STOCK_API_KEY"):
            sources.append(
                {
                    "id": "stock_default",
                    "type": "stock",
                    "enabled": True,
                    "schedule": "0 9-16 * * 1-5",
                    "config": {},
                    "rendering": {
                        "layout": "default",
                        "background": "local",
                        "background_query": "stock/charts",
                    },
                }
            )

        # Detect System Health (always include if any sources are configured)
        if sources:
            sources.append(
                {
                    "id": "system_health_default",
                    "type": "system_health",
                    "enabled": True,
                    "schedule": "*/5 * * * *",
                    "config": {},
                    "rendering": {
                        "layout": "default",
                        "background": "gradient",
                    },
                }
            )

        # Detect Ferry Map (as alternative to ferry source)
        if os.getenv("FERRY_ROUTE"):
            sources.append(
                {
                    "id": "ferry_map_default",
                    "type": "ferry_map",
                    "enabled": False,
                    "schedule": "*/10 6-22 * * *",
                    "config": {},
                    "rendering": {
                        "layout": "full_map",
                        "background": "ferry_map",
                    },
                }
            )

        return {"sources": sources}

    def write_config(self, output_path: Path = Path("sources.yaml")) -> None:
        """Write generated config to file."""
        config = self.migrate()

        if output_path.exists():
            print(f"⚠️  File {output_path} already exists!")
            response = input("Overwrite? (y/N): ")
            if response.lower() != "y":
                print("Migration cancelled.")
                return

        with open(output_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)

        print(f"✓ Generated {output_path}")
        print(f"✓ Found {len(config['sources'])} source(s)")

        if config["sources"]:
            print("\nConfigured sources:")
            for source in config["sources"]:
                print(f"  - {source['id']} ({source['type']})")

        print("\nNext steps:")
        print("  1. Review the generated file and adjust schedules as needed")
        print("  2. Run: python generate_signage.py")
        print("  3. The plugin system will be used automatically!")
