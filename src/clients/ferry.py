"""
Ferry schedule and status client for Washington State Ferries.
Fetches real-time data from WSDOT Ferries API.
"""

import logging
import re
from datetime import datetime
from typing import List, Optional, Dict, Any

from src.clients.base import APIClient
from src.config import Config
from src.models.signage_data import (
    FerryData,
    FerrySchedule,
    FerryVessel,
)

logger = logging.getLogger(__name__)


# Terminal ID mappings for Fauntleroy-Southworth route
TERMINAL_IDS = {
    "Fauntleroy": 9,
    "Southworth": 20,
}

# Route ID for Fauntleroy-Southworth
ROUTE_ID = 13


class FerryClient(APIClient):
    """Client for WSDOT Ferries API."""
    
    SCHEDULE_BASE_URL = "https://www.wsdot.wa.gov/Ferries/API/Schedule/rest"
    VESSEL_BASE_URL = "https://www.wsdot.wa.gov/Ferries/API/Vessels/rest"
    
    def __init__(self):
        """Initialize with ferry route from config."""
        # Use longer timeout for slow WSDOT API
        super().__init__(timeout=30, max_retries=2)
        
        self.route = Config.FERRY_ROUTE
        self.home_terminal = Config.FERRY_HOME_TERMINAL
        self.api_key = Config.WSDOT_API_KEY
        
        if not self.route:
            logger.warning("FERRY_ROUTE not configured")
        if not self.api_key:
            logger.warning("WSDOT_API_KEY not configured")
    
    def get_ferry_data(self) -> Optional[FerryData]:
        """
        Fetch comprehensive ferry data: schedule, vessels, alerts.
        
        Returns:
            FerryData object or None on failure
        """
        if not self.route or not self.api_key:
            logger.warning("Ferry configuration incomplete")
            return self._get_stub_data()
        
        try:
            # Get today's date for API calls
            today = datetime.now().strftime("%Y-%m-%d")
            
            # Fetch all data in parallel (conceptually)
            schedule = self._get_schedule(today)
            vessels = self._get_vessel_locations()
            alerts = self._get_alerts()
            wait_time = self._get_wait_time()
            
            # Parse status from alerts
            status, delay_minutes = self._parse_status_from_alerts(alerts)
            
            # Split schedule by direction
            southworth_departures = []
            fauntleroy_departures = []
            
            for sailing in schedule:
                if sailing.departing_terminal == "Southworth":
                    southworth_departures.append(sailing)
                elif sailing.departing_terminal == "Fauntleroy":
                    fauntleroy_departures.append(sailing)
            
            return FerryData(
                route=self.route,
                status=status,
                delay_minutes=delay_minutes,
                southworth_departures=southworth_departures[:5],  # Next 5 sailings
                fauntleroy_departures=fauntleroy_departures[:5],
                vessels=vessels,
                alerts=alerts,
                wait_time_minutes=wait_time
            )
            
        except Exception as e:
            logger.error(f"Failed to fetch ferry data: {e}")
            return None
    
    def _get_stub_data(self) -> FerryData:
        """Return stub data when API is not configured."""
        logger.warning("Using stub ferry data - configure WSDOT_API_KEY for real data")
        return FerryData(
            route=self.route or "Fauntleroy-Southworth",
            status="normal",
            delay_minutes=0,
            southworth_departures=[],
            fauntleroy_departures=[],
            vessels=[],
            alerts=[],
            wait_time_minutes=None
        )
    
    def _get_schedule(self, trip_date: str) -> List[FerrySchedule]:
        """
        Fetch ferry schedule for route.
        
        Args:
            trip_date: Date in YYYY-MM-DD format
            
        Returns:
            List of FerrySchedule objects for today's sailings
        """
        try:
            # Use basic schedule endpoint (faster than scheduletoday)
            url = f"{self.SCHEDULE_BASE_URL}/schedule/{trip_date}/{ROUTE_ID}"
            params = {"apiaccesscode": self.api_key}
            
            response = self._make_request(url, params=params)
            if not response:
                logger.warning("Failed to fetch schedule, using stub data")
                return []
            
            data = response.json()
            schedules = []
            current_time = datetime.now()
            
            # API returns nested structure with TerminalCombos
            terminal_combos = data.get("TerminalCombos", [])
            
            for combo in terminal_combos:
                departing_terminal = combo.get("DepartingTerminalName", "")
                arriving_terminal = combo.get("ArrivingTerminalName", "")
                
                # Get all sailing times for this terminal pair
                times = combo.get("Times", [])
                
                for sailing in times:
                    # Parse .NET date format: /Date(milliseconds-timezone)/
                    departing_time_str = sailing.get("DepartingTime", "")
                    departure_dt, departure_time = self._parse_dotnet_date(departing_time_str)
                    
                    if not departure_time:
                        continue
                    
                    # Only include future sailings
                    if departure_dt and departure_dt < current_time:
                        continue
                    
                    schedules.append(FerrySchedule(
                        departure_time=departure_time,
                        arrival_time="",  # Not provided by API
                        vessel_name=sailing.get("VesselName", ""),
                        departing_terminal=departing_terminal
                    ))
            
            return schedules
            
        except Exception as e:
            logger.error(f"Failed to fetch ferry schedule: {e}")
            return []
    
    def _parse_dotnet_date(self, date_str: str) -> tuple[Optional[datetime], str]:
        """
        Parse .NET JSON date format to readable time.
        
        Args:
            date_str: .NET date like "/Date(1764052500000-0800)/"
            
        Returns:
            Tuple of (datetime object, time string like "10:15 AM")
        """
        try:
            # Extract milliseconds from /Date(milliseconds-timezone)/
            import re
            match = re.search(r'/Date\((\d+)([+-]\d{4})?\)/', date_str)
            if not match:
                return None, ""
            
            milliseconds = int(match.group(1))
            
            # Convert to datetime
            dt = datetime.fromtimestamp(milliseconds / 1000.0)
            
            # Format as 12-hour time
            time_str = dt.strftime("%I:%M %p").lstrip('0')
            
            return dt, time_str
            
        except Exception as e:
            logger.debug(f"Failed to parse date {date_str}: {e}")
            return None, ""
    
    def _get_terminal_name(self, terminal_id: Optional[int]) -> str:
        """Map terminal ID to name."""
        id_to_name = {v: k for k, v in TERMINAL_IDS.items()}
        return id_to_name.get(terminal_id, f"Terminal {terminal_id}")
    
    def _get_vessel_locations(self) -> List[FerryVessel]:
        """
        Fetch real-time vessel positions for all active vessels.
        
        Returns:
            List of FerryVessel objects with current locations
        """
        try:
            url = f"{self.VESSEL_BASE_URL}/vessellocations"
            params = {"apiaccesscode": self.api_key}
            
            response = self._make_request(url, params=params)
            if not response:
                return []
            
            data = response.json()
            vessels = []
            
            for vessel_data in data:
                if not isinstance(vessel_data, dict):
                    continue
                
                # Only include vessels on our route
                vessel_route_id = vessel_data.get("RouteID")
                if vessel_route_id != ROUTE_ID:
                    continue
                
                name = vessel_data.get("VesselName", "")
                latitude = vessel_data.get("Latitude")
                longitude = vessel_data.get("Longitude")
                
                # Skip vessels without location data
                if latitude is None or longitude is None:
                    continue
                
                # Determine heading/direction from speed and heading
                heading = vessel_data.get("Heading", 0)
                speed = vessel_data.get("Speed", 0)
                
                vessels.append(FerryVessel(
                    name=name,
                    latitude=latitude,
                    longitude=longitude,
                    speed=speed,
                    heading=heading
                ))
            
            return vessels
            
        except Exception as e:
            logger.error(f"Failed to fetch vessel locations: {e}")
            return []
    
    def _get_alerts(self) -> List[str]:
        """
        Fetch service alerts for the ferry system.
        
        Returns:
            List of alert messages (strings)
        """
        try:
            url = f"{self.SCHEDULE_BASE_URL}/alerts"
            params = {"apiaccesscode": self.api_key}
            
            response = self._make_request(url, params=params)
            if not response:
                return []
            
            data = response.json()
            alerts = []
            
            for alert in data:
                if not isinstance(alert, dict):
                    continue
                
                # Check if alert is relevant to our route
                alert_route_id = alert.get("RouteID")
                if alert_route_id and alert_route_id != ROUTE_ID:
                    continue
                
                # Get alert bulletin text
                bulletin = alert.get("BulletinTitle", "")
                if bulletin:
                    alerts.append(bulletin)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Failed to fetch ferry alerts: {e}")
            return []
    
    def _get_wait_time(self) -> Optional[int]:
        """
        Fetch current wait time at home terminal.
        
        Note: WSDOT API doesn't provide real-time wait times directly.
        This would need to be scraped from the website or estimated.
        
        Returns:
            Wait time in minutes, or None if unavailable
        """
        # Not available via REST API
        return None
    
    def _parse_status_from_alerts(
        self,
        alerts: List[str]
    ) -> tuple[str, int]:
        """
        Determine service status from alert text.
        
        Returns:
            Tuple of (status, delay_minutes)
        """
        status = "normal"
        delay_minutes = 0
        
        for alert in alerts:
            alert_lower = alert.lower()
            
            # Check for cancellation
            if "cancel" in alert_lower or "not operating" in alert_lower:
                status = "cancelled"
                break
            
            # Check for delays
            if "delay" in alert_lower:
                status = "delayed"
                
                # Try to extract delay minutes from alert text
                match = re.search(r"(\d+)\s*min", alert_lower)
                if match:
                    delay_minutes = int(match.group(1))
        
        return status, delay_minutes


class FerryWebScraper:
    """
    Fallback web scraper for ferry data when API is unavailable.
    Not yet implemented.
    """
    
    def __init__(self):
        """Initialize scraper."""
        logger.warning(
            "FerryWebScraper is a stub - web scraping fallback not implemented"
        )
    
    def get_ferry_data(self) -> Optional[FerryData]:
        """Scrape ferry data from website."""
        logger.warning("Web scraping fallback called but not implemented")
        return None
