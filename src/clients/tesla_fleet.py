"""
Tesla Fleet API client for vehicle and energy product data.
Uses OAuth2 client credentials flow for authentication.
"""

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

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
                with open(self.TOKEN_FILE, "r") as f:
                    data = json.load(f)
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")  # For third-party tokens
                    expires_at_str = data.get("expires_at")
                    if expires_at_str:
                        self.token_expires_at = datetime.fromisoformat(expires_at_str)
                    logger.debug("Loaded existing Tesla tokens")
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
                    data.get("refresh_token")  # New refresh token
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

    def _api_request(self, endpoint: str, method: str = "GET") -> Optional[dict[str, Any]]:
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
            logger.error(f"API request failed with {response.status_code}: {response.text}")
        
        return None

    def get_vehicles(self) -> Optional[list[dict[str, Any]]]:
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

    def get_vehicle_data(self, vehicle_id: str) -> Optional[dict[str, Any]]:
        """
        Get vehicle data (battery, range, location, etc.).
        
        Args:
            vehicle_id: Vehicle ID
            
        Returns:
            Vehicle data dict or None
        """
        data = self._api_request(f"/api/1/vehicles/{vehicle_id}/vehicle_data")
        
        if data and "response" in data:
            return data["response"]
        
        return None

    def get_energy_sites(self) -> Optional[list[dict[str, Any]]]:
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

    def get_energy_site_data(self, site_id: str) -> Optional[dict[str, Any]]:
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
