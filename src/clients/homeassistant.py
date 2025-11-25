"""
Home Assistant API client.
Fetches entity states from Home Assistant.
"""

import logging
from typing import Dict, Tuple

from src.clients.base import APIClient
from src.config import Config

logger = logging.getLogger(__name__)


class HomeAssistantClient(APIClient):
    """Client for Home Assistant REST API."""
    
    def __init__(self):
        """Initialize with HA URL and token from config."""
        super().__init__()
        
        if not Config.HA_URL or not Config.HA_TOKEN:
            raise ValueError("HA_URL and HA_TOKEN must be configured")
        
        self.base_url = Config.HA_URL.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {Config.HA_TOKEN}",
            "Content-Type": "application/json"
        }
    
    def get_entity_state(self, entity_id: str) -> Tuple[str, Dict]:
        """
        Get state and attributes for a Home Assistant entity.
        
        Args:
            entity_id: Entity ID (e.g., 'sensor.tesla_battery')
        
        Returns:
            Tuple of (state, attributes dict)
            Returns ("N/A", {}) on failure
        """
        url = f"{self.base_url}/api/states/{entity_id}"
        
        response = self._make_request(url, headers=self.headers)
        
        if not response:
            logger.error(f"Failed to fetch entity state: {entity_id}")
            return "N/A", {}
        
        try:
            data = response.json()
            state = data.get("state", "N/A")
            attributes = data.get("attributes", {})
            
            logger.debug(f"Fetched {entity_id}: {state}")
            return state, attributes
        
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse HA response for {entity_id}: {e}")
            return "N/A", {}
