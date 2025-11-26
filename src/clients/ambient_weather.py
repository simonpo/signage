"""
Ambient Weather API client for personal weather station data.
Fetches real-time hyper-local weather from user's Ambient Weather device.
"""

import json
import logging
from datetime import datetime
from typing import Optional

from src.clients.base import APIClient
from src.config import Config
from src.models.signage_data import (
    AmbientMultiSensorData,
    AmbientSensorData,
    AmbientWeatherData,
)

logger = logging.getLogger(__name__)


class AmbientWeatherClient(APIClient):
    """Client for Ambient Weather REST API."""

    BASE_URL = "https://rt.ambientweather.net/v1/devices"

    def __init__(self):
        """Initialize with API keys from config."""
        super().__init__()

        if not Config.AMBIENT_API_KEY:
            raise ValueError("AMBIENT_API_KEY must be configured")
        if not Config.AMBIENT_APP_KEY:
            raise ValueError("AMBIENT_APP_KEY must be configured")

        self.api_key = Config.AMBIENT_API_KEY
        self.app_key = Config.AMBIENT_APP_KEY

    def get_weather(self, include_trend: bool = True) -> Optional[AmbientWeatherData]:
        """
        Fetch current weather from user's Ambient Weather station.

        Args:
            include_trend: If True, calculates pressure trend from recent history

        Returns:
            AmbientWeatherData object or None on failure
        """
        params = {"apiKey": self.api_key, "applicationKey": self.app_key}

        response = self._make_request(self.BASE_URL, params=params)

        if not response:
            logger.error("Failed to fetch Ambient Weather data")
            return None

        try:
            data = response.json()

            # API returns array of devices, get first one
            if not data or len(data) == 0:
                logger.error("No devices found in Ambient Weather account")
                return None

            device = data[0]
            last_data = device.get("lastData", {})
            info = device.get("info", {})

            # Get station name
            station_name = info.get("name", "Weather Station")

            # Required fields
            tempf = last_data.get("tempf")
            humidity = last_data.get("humidity")
            windspeedmph = last_data.get("windspeedmph", 0)
            winddir = last_data.get("winddir", 0)
            baromrelin = last_data.get("baromrelin")
            feels_like = last_data.get("feelsLike")
            dew_point = last_data.get("dewPoint")
            dailyrainin = last_data.get("dailyrainin", 0)
            hourlyrainin = last_data.get("hourlyrainin", 0)

            # Validate required fields
            if None in [tempf, humidity, baromrelin, feels_like, dew_point]:
                logger.error("Missing required weather data fields")
                return None

            # Optional fields
            temp_high = last_data.get("tempf_high")  # May not be available
            temp_low = last_data.get("tempf_low")
            solarradiation = last_data.get("solarradiation")
            uv = last_data.get("uv")

            # Indoor air quality
            pm25_in = last_data.get("pm25_in")
            aqi_pm25_in = last_data.get("pm25_in_aqin")
            co2_in = last_data.get("co2_in")
            tempinf = last_data.get("tempinf")
            humidityin = last_data.get("humidityin")

            weather = AmbientWeatherData(
                station_name=station_name,
                tempf=tempf,
                humidity=humidity,
                windspeedmph=windspeedmph,
                winddir=winddir,
                baromrelin=baromrelin,
                feels_like=feels_like,
                dew_point=dew_point,
                dailyrainin=dailyrainin,
                hourlyrainin=hourlyrainin,
                temp_high=temp_high,
                temp_low=temp_low,
                solarradiation=solarradiation,
                uv=uv,
                pm25_in=pm25_in,
                aqi_pm25_in=aqi_pm25_in,
                co2_in=co2_in,
                tempinf=tempinf,
                humidityin=humidityin,
            )

            logger.info(
                f"Ambient Weather: {tempf}°F, Humidity: {humidity}%, " f"Wind: {windspeedmph} mph"
            )
            return weather

        except (ValueError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse Ambient Weather response: {e}")
            return None

    def get_all_sensors(self) -> Optional[AmbientMultiSensorData]:
        """
        Fetch all sensor data from user's Ambient Weather station.
        Includes all temp1f-temp10f and humidity1-humidity10 sensors.

        Returns:
            AmbientMultiSensorData object or None on failure
        """
        params = {"apiKey": self.api_key, "applicationKey": self.app_key}

        response = self._make_request(self.BASE_URL, params=params)

        if not response:
            logger.error("Failed to fetch Ambient Weather data")
            return None

        try:
            data = response.json()

            if not data or len(data) == 0:
                logger.error("No devices found in Ambient Weather account")
                return None

            device = data[0]
            last_data = device.get("lastData", {})
            info = device.get("info", {})

            # Get station info
            station_name = info.get("name", "Weather Station")
            outdoor_temp = last_data.get("tempf")
            outdoor_humidity = last_data.get("humidity")

            if outdoor_temp is None or outdoor_humidity is None:
                logger.error("Missing outdoor temperature/humidity data")
                return None

            # Parse sensor name mappings from config
            try:
                sensor_names = json.loads(Config.AMBIENT_SENSOR_NAMES)
            except json.JSONDecodeError:
                logger.warning("Invalid AMBIENT_SENSOR_NAMES JSON, using defaults")
                sensor_names = {}

            # Collect all sensor data
            sensors = []
            for i in range(1, 11):  # Sensors 1-10
                temp_key = f"temp{i}f"
                hum_key = f"humidity{i}"
                batt_key = f"batt{i}"

                temp = last_data.get(temp_key)
                humidity = last_data.get(hum_key)
                battery = last_data.get(batt_key)

                # Only include sensors that have at least temp or humidity
                if temp is not None or humidity is not None:
                    # Get friendly name or use default
                    name = sensor_names.get(str(i), f"Sensor {i}")

                    # Battery: 1=OK, 0=Low (or None if not available)
                    battery_ok = battery == 1 if battery is not None else None

                    sensors.append(
                        AmbientSensorData(
                            name=name, temperature=temp, humidity=humidity, battery_ok=battery_ok
                        )
                    )

            # Get timestamp
            dateutc = last_data.get("dateutc")
            if dateutc:
                timestamp = datetime.fromtimestamp(dateutc / 1000.0)
                last_updated = timestamp.strftime("%I:%M %p").lstrip("0")
            else:
                last_updated = None

            multi_sensor_data = AmbientMultiSensorData(
                station_name=station_name,
                outdoor_temp=outdoor_temp,
                outdoor_humidity=outdoor_humidity,
                sensors=sensors,
                last_updated=last_updated,
            )

            logger.info(f"Ambient Sensors: {len(sensors)} sensors found")
            return multi_sensor_data

        except (ValueError, KeyError, IndexError) as e:
            logger.error(f"Failed to parse Ambient Weather sensor data: {e}")
            return None
