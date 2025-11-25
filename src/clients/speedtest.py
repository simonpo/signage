"""
Speedtest Tracker API client.
Fetches latest internet speed test results from local Speedtest Tracker instance.
"""

import logging
from datetime import datetime
from typing import Optional

from src.clients.base import APIClient
from src.config import Config
from src.models.signage_data import SpeedtestData

logger = logging.getLogger(__name__)


class SpeedtestClient(APIClient):
    """Client for Speedtest Tracker API."""
    
    def __init__(self):
        """Initialize with config from environment."""
        super().__init__()
        
        if not Config.SPEEDTEST_URL:
            raise ValueError("SPEEDTEST_URL must be configured")
        if not Config.SPEEDTEST_TOKEN:
            raise ValueError("SPEEDTEST_TOKEN must be configured")
        
        self.base_url = Config.SPEEDTEST_URL.rstrip('/')
        self.token = Config.SPEEDTEST_TOKEN
    
    def get_latest(self) -> Optional[SpeedtestData]:
        """
        Fetch latest speedtest results.
        
        Returns:
            SpeedtestData object or None on failure
        """
        url = f"{self.base_url}/api/speedtest/latest"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json"
        }
        
        response = self._make_request(url, headers=headers)
        
        if not response:
            logger.error("Failed to fetch speedtest data")
            return None
        
        try:
            result = response.json()
            
            if result.get("message") != "ok":
                logger.error(f"API returned error: {result}")
                return None
            
            data = result.get("data", {})
            
            # Required fields
            download = data.get("download")
            upload = data.get("upload")
            ping = data.get("ping")
            server_name = data.get("server_name", "Unknown")
            server_host = data.get("server_host", "")
            created_at = data.get("created_at")
            
            if None in [download, upload, ping]:
                logger.error("Missing required speedtest fields")
                return None
            
            # Format timestamp
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    timestamp = dt.strftime("%b %d, %I:%M %p").replace(' 0', ' ')
                except (ValueError, AttributeError):
                    timestamp = "Unknown"
            else:
                timestamp = "Unknown"
            
            speedtest = SpeedtestData(
                download=download,
                upload=upload,
                ping=ping,
                server_name=server_name,
                server_host=server_host,
                timestamp=timestamp,
                url=data.get("url")
            )
            
            logger.info(
                f"Speedtest: ↓{download:.1f} Mbps, ↑{upload:.1f} Mbps, "
                f"{ping:.1f}ms ping"
            )
            return speedtest
        
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse speedtest response: {e}")
            return None
