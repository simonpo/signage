"""
Tesla Fleet API client for vehicle and energy product data.
Uses OAuth2 client credentials flow for authentication.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests

from src.clients.base import APIClient
from src.config import Config

logger = logging.getLogger(__name__)


class TeslaFleetClient(APIClient):
    """
    Client for Tesla Fleet API.

    Supports:
    - Vehicle data (battery, range, location, charging)
    - Energy products (Powerwall battery, grid status, solar)
    """

    # Regional endpoints
    REGIONS = {
        "na": "https://fleet-api.prd.na.vn.cloud.tesla.com",
        "eu": "https://fleet-api.prd.eu.vn.cloud.tesla.com",
        "cn": "https://fleet-api.prd.cn.vn.cloud.tesla.cn",
    }

    AUTH_URL = "https://fleet-auth.prd.vn.cloud.tesla.com/oauth2/v3/token"

    TOKEN_FILE = Path(".tesla_tokens.json")
    VEHICLE_CACHE_FILE = Path(".cache/tesla_vehicle_data.json")

    def __init__(self):
        """Initialize Tesla Fleet client."""
        super().__init__()

        if not Config.TESLA_CLIENT_ID or not Config.TESLA_CLIENT_SECRET:
            raise ValueError("TESLA_CLIENT_ID and TESLA_CLIENT_SECRET must be configured")

        self.client_id = Config.TESLA_CLIENT_ID
        self.client_secret = Config.TESLA_CLIENT_SECRET
        self.region = Config.TESLA_REGION or "na"
        self.base_url = self.REGIONS.get(self.region, self.REGIONS["na"])

        self.access_token = None
        self.refresh_token = None  # For third-party tokens
        self.token_expires_at = None

        # Load existing tokens if available
        self._load_tokens()

    def _load_tokens(self):
        """Load tokens from file if they exist."""
        if self.TOKEN_FILE.exists():
            try:
                with open(self.TOKEN_FILE) as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")  # For third-party tokens
                    expires_at_str = data.get("expires_at")
                    if expires_at_str:
                        self.token_expires_at = datetime.fromisoformat(expires_at_str)
                        time_remaining = self.token_expires_at - datetime.now()
                        logger.debug(
                            f"Loaded Tesla tokens (expires in {time_remaining.total_seconds()/3600:.1f}h)"
                        )
            except Exception as e:
                logger.warning(f"Failed to load tokens: {e}")

    def _save_tokens(self, access_token: str, expires_in: int, refresh_token: str = None):
        """Save tokens to file."""
        self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

        try:
            token_data = {
                "access_token": access_token,
                "expires_at": self.token_expires_at.isoformat(),
            }
            if self.refresh_token:
                token_data["refresh_token"] = self.refresh_token

            with open(self.TOKEN_FILE, "w") as f:
                json.dump(token_data, f)
            logger.debug("Saved Tesla tokens")
        except Exception as e:
            logger.warning(f"Failed to save tokens: {e}")

    def _ensure_token(self):
        """Ensure we have a valid access token."""
        # Check if token exists and is not expired
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at - timedelta(minutes=5):
                return  # Token is still valid

        # Try refresh token first (for third-party/personal use)
        if self.refresh_token:
            logger.info("Refreshing Tesla access token")

            payload = {
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "refresh_token": self.refresh_token,
            }

            try:
                response = requests.post(
                    self.AUTH_URL,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                    timeout=self.timeout,
                )
                response.raise_for_status()

                data = response.json()
                self._save_tokens(
                    data["access_token"],
                    data["expires_in"],
                    data.get("refresh_token"),  # New refresh token
                )
                logger.info("Successfully refreshed Tesla access token")
                return

            except Exception as e:
                logger.warning(f"Failed to refresh token: {e}")
                # Fall through to try client_credentials

        # Fallback: try client_credentials (for partner use)
        logger.info("Requesting new Tesla Fleet API token via client_credentials")

        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "openid vehicle_device_data vehicle_location energy_device_data",
            "audience": self.base_url,
        }

        try:
            response = requests.post(
                self.AUTH_URL,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self.timeout,
            )
            response.raise_for_status()

            data = response.json()
            self._save_tokens(data["access_token"], data["expires_in"])
            logger.info("Successfully obtained Tesla Fleet API token")

        except Exception as e:
            logger.error(f"Failed to obtain Tesla token: {e}")
            logger.error("Please run: python oauth_tesla.py")
            raise

    def _api_request(self, endpoint: str, method: str = "GET") -> dict[str, Any] | None:
        """
        Make authenticated API request.

        Args:
            endpoint: API endpoint (e.g., "/api/1/vehicles")
            method: HTTP method

        Returns:
            Response data or None on failure
        """
        self._ensure_token()

        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

        response = self._make_request(url, method=method, headers=headers)

        if response and response.status_code == 200:
            return response.json()
        elif response:
            # 408 timeouts are expected for sleeping vehicles
            if response.status_code == 408:
                logger.warning(
                    "Vehicle unavailable (408 timeout) - likely asleep or out of connectivity"
                )
            # 401/403 suggest auth issues
            elif response.status_code in [401, 403]:
                logger.error(
                    f"Authentication failed ({response.status_code}). "
                    "Token may be expired or invalid. Run: python oauth_tesla.py"
                )
            else:
                logger.error(f"API request failed with {response.status_code}: {response.text}")

        return None

    def get_vehicles(self) -> list[dict[str, Any]] | None:
        """
        Get list of vehicles.

        Returns:
            List of vehicle objects
        """
        data = self._api_request("/api/1/vehicles")

        if data and "response" in data:
            vehicles = data["response"]
            logger.info(f"Found {len(vehicles)} vehicle(s)")
            return vehicles

        return None

    def get_vehicle_data(self, vehicle_id: str) -> dict[str, Any] | None:
        """
        Get detailed vehicle data (battery, location, climate, etc).
        Caches successful responses for fallback when vehicle is asleep.

        Args:
            vehicle_id: Vehicle ID string

        Returns:
            Vehicle data dictionary or None
        """
        endpoint = f"/api/1/vehicles/{vehicle_id}/vehicle_data"
        data = self._api_request(endpoint)

        if data and "response" in data:
            vehicle_data = data["response"]
            # Cache successful response
            self._cache_vehicle_data(vehicle_id, vehicle_data)
            return vehicle_data

        return None

    def get_cached_vehicle_data(self, vehicle_id: str) -> dict[str, Any] | None:
        """
        Get cached vehicle data from last successful fetch.

        Args:
            vehicle_id: Vehicle ID string

        Returns:
            Dict with 'data' and 'cached_at' keys, or None if no cache exists
        """
        if not self.VEHICLE_CACHE_FILE.exists():
            return None

        try:
            with open(self.VEHICLE_CACHE_FILE) as f:
                cache = json.load(f)
                vehicle_cache = cache.get(vehicle_id)
                if vehicle_cache:
                    return vehicle_cache
        except Exception as e:
            logger.debug(f"Failed to load cached vehicle data: {e}")

        return None

    def _cache_vehicle_data(self, vehicle_id: str, data: dict[str, Any]) -> None:
        """
        Cache vehicle data for fallback use.

        Args:
            vehicle_id: Vehicle ID string
            data: Vehicle data to cache
        """
        try:
            # Ensure cache directory exists
            self.VEHICLE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

            # Load existing cache or create new
            cache = {}
            if self.VEHICLE_CACHE_FILE.exists():
                with open(self.VEHICLE_CACHE_FILE) as f:
                    cache = json.load(f)

            # Store data with timestamp
            cache[vehicle_id] = {
                "data": data,
                "cached_at": datetime.now().isoformat(),
            }

            # Write back to file
            with open(self.VEHICLE_CACHE_FILE, "w") as f:
                json.dump(cache, f, indent=2)

            logger.debug(f"Cached vehicle data for {vehicle_id}")
        except Exception as e:
            logger.debug(f"Failed to cache vehicle data: {e}")

    def get_energy_sites(self) -> list[dict[str, Any]] | None:
        """
        Get list of energy sites (Powerwalls, Solar, etc.).

        Returns:
            List of energy site objects
        """
        data = self._api_request("/api/1/energy_sites")

        if data and "response" in data:
            sites = data["response"]
            logger.info(f"Found {len(sites)} energy site(s)")
            return sites

        return None

    def get_energy_site_data(self, site_id: str) -> dict[str, Any] | None:
        """
        Get energy site data (battery %, grid status, solar production).

        Args:
            site_id: Energy site ID

        Returns:
            Energy site data dict or None
        """
        data = self._api_request(f"/api/1/energy_sites/{site_id}/live_status")

        if data and "response" in data:
            return data["response"]

        return None
