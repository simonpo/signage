"""
Tesla data source plugin.
Wraps Tesla functionality from existing codebase.
"""

import logging

from src.clients.tesla_fleet import TeslaFleetClient
from src.models.signage_data import SignageContent, TeslaData
from src.plugins.base_source import BaseSource
from src.plugins.registry import SourceRegistry

logger = logging.getLogger(__name__)


@SourceRegistry.register("tesla")
class TeslaSource(BaseSource):
    """Tesla data source plugin."""

    def validate_config(self) -> bool:
        """Validate Tesla config."""
        # vehicle_index is optional, defaults to 0
        if "vehicle_index" in self.config:
            index = self.config["vehicle_index"]
            if not isinstance(index, int) or index < 0:
                raise ValueError("vehicle_index must be a non-negative integer")
        return True

    def fetch_data(self) -> SignageContent | None:
        """Fetch Tesla vehicle data."""
        vehicle_index = self.config.get("vehicle_index", 0)

        logger.info(f"[{self.source_id}] Fetching Tesla vehicle data (index: {vehicle_index})")

        try:
            client = TeslaFleetClient()
            vehicles = client.get_vehicles()

            if not vehicles or len(vehicles) <= vehicle_index:
                logger.warning(
                    f"[{self.source_id}] Vehicle at index {vehicle_index} not found "
                    f"(total vehicles: {len(vehicles) if vehicles else 0})"
                )
                return None

            vehicle = vehicles[vehicle_index]
            vehicle_id = vehicle["id"]
            vehicle_name = vehicle.get("display_name", "Tesla")

            # Get vehicle data
            vehicle_data = client.get_vehicle_data(str(vehicle_id))

            if not vehicle_data:
                # Try cached data
                cached_data = client.get_cached_vehicle_data(str(vehicle_id))
                if cached_data:
                    vehicle_data = cached_data["data"]
                    logger.info(
                        f"[{self.source_id}] Using cached data from {cached_data['cached_at']}"
                    )
                else:
                    logger.warning(f"[{self.source_id}] No vehicle data available")
                    return None

            # Extract data (simplified version - in production, would extract all fields)
            charge_state = vehicle_data.get("charge_state", {})
            climate_state = vehicle_data.get("climate_state", {})
            vehicle_state = vehicle_data.get("vehicle_state", {})

            battery_level = charge_state.get("battery_level")
            battery_range = charge_state.get("battery_range")
            charging_state = charge_state.get("charging_state", "")

            if battery_level is None or battery_range is None:
                logger.warning(f"[{self.source_id}] Incomplete vehicle data")
                return None

            # Create minimal TeslaData for now
            # (In production, would populate all fields like in generate_signage.py)
            tesla_data = TeslaData(
                vehicle_name=vehicle_name,
                battery_level=str(battery_level),
                battery_unit="%",
                range=str(int(battery_range)),
                range_unit=" mi",
                charging_state=charging_state,
                charge_limit_soc=charge_state.get("charge_limit_soc", 0),
                time_to_full=str(charge_state.get("time_to_full_charge", "")),
                charger_power=charge_state.get("charger_power", 0.0),
                plugged_in=charge_state.get("conn_charge_cable", "Disconnected") != "Disconnected",
                odometer=vehicle_state.get("odometer", 0.0),
                inside_temp=climate_state.get("inside_temp", 0.0),
                outside_temp=climate_state.get("outside_temp", 0.0),
                climate_on=climate_state.get("is_climate_on", False),
                defrost_on=climate_state.get("defrost_mode", 0) == 1,
                software_version=vehicle_state.get("software_version", ""),
                locked=vehicle_state.get("locked", False),
                sentry_mode=vehicle_state.get("sentry_mode", False),
                latitude=0.0,
                longitude=0.0,
                heading=0,
                shift_state="",
                speed=0.0,
                tire_pressure={},
                last_seen="",
                online=vehicle.get("state", "online") == "online",
                location_display="",
                cached_at=None,
            )

            return tesla_data.to_signage()

        except Exception as e:
            logger.error(f"[{self.source_id}] Failed to fetch Tesla data: {e}")
            return None
