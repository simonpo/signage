"""
Full-screen ferry map renderer showing all WSF vessel positions.
Renders real-time ferry locations across Puget Sound with satellite imagery.
"""

import logging
from datetime import datetime, timedelta
from io import BytesIO
from typing import List, Optional, Tuple

import requests
from PIL import Image, ImageDraw, ImageFont

from src.config import Config
from src.models.signage_data import FerryVessel

logger = logging.getLogger(__name__)


class FerryMapRenderer:
    """
    Renders full-screen ferry map with all vessel positions.
    Covers Puget Sound ferry routes with optional satellite imagery.
    """

    # Puget Sound bounds for full ferry system
    MIN_LAT = 47.0
    MAX_LAT = 48.7
    MIN_LON = -123.0
    MAX_LON = -122.0

    # Center point for map - focused on central Puget Sound
    # (Southworth-Vashon-Fauntleroy and Bremerton-Seattle routes)
    # Blake Island positioned 5% below center
    CENTER_LAT = 47.575  # Fine-tuned positioning
    CENTER_LON = -122.49  # Blake Island longitude

    # Full 4K resolution
    MAP_WIDTH = Config.IMAGE_WIDTH
    MAP_HEIGHT = Config.IMAGE_HEIGHT

    # Margins
    MARGIN = 100

    # Colors
    WATER_COLOR = (41, 98, 150)  # Deep blue water
    LAND_COLOR = (76, 112, 68)  # Muted green
    ROUTE_COLOR = (255, 255, 255, 100)  # Semi-transparent white
    VESSEL_COLOR = (255, 193, 7)  # Amber/gold
    TERMINAL_COLOR = (220, 53, 69)  # Red
    TEXT_COLOR = (255, 255, 255)  # White

    def __init__(self):
        """Initialize map renderer."""
        self.title_font = self._load_font(120)
        self.label_font = self._load_font(50)
        self.small_font = self._load_font(40)
        self.google_maps_key = getattr(Config, "GOOGLE_MAPS_API_KEY", None)

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        """Load font at specified size."""
        try:
            return ImageFont.truetype(Config.FONT_PATH, size)
        except Exception:
            return ImageFont.load_default()

    def _fetch_satellite_map(self) -> Optional[Image.Image]:
        """
        Fetch satellite imagery from Google Maps Static API with one-week caching.
        Cached images are stored in .cache/ferry_map_bg.jpg and refreshed weekly.

        Returns:
            Satellite image or None if unavailable
        """
        if not self.google_maps_key:
            logger.info("No Google Maps API key configured, using solid background")
            return None

        # Check cache first
        cache_file = Config.CACHE_PATH / "ferry_map_bg.jpg"
        cache_age_days = 30  # Refresh monthly

        if cache_file.exists():
            cache_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            age = datetime.now() - cache_time

            if age < timedelta(days=cache_age_days):
                logger.info(f"Using cached satellite imagery (age: {age.days} days)")
                try:
                    img = Image.open(cache_file)
                    return img
                except Exception as e:
                    logger.warning(f"Failed to load cached image: {e}")
                    # Fall through to fetch new image

        try:
            # Google Maps Static API URL
            # Request in 16:9 aspect ratio to match 4K display
            # Max size is 640x640 for free tier, so we'll request multiple tiles
            # or just use 640x360 and scale up

            url = "https://maps.googleapis.com/maps/api/staticmap"

            # Calculate bounds to cover Puget Sound
            # Using zoom level and center that shows all ferries
            params = {
                "center": f"{self.CENTER_LAT},{self.CENTER_LON}",
                "zoom": "11",  # Zoomed in to focus on central routes
                "size": "640x360",  # 16:9 aspect ratio
                "maptype": "satellite",
                "key": self.google_maps_key,
                "scale": "2",  # Get 1280x720 on retina displays
            }

            logger.info("Fetching satellite imagery from Google Maps...")
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                # Scale up to 4K maintaining aspect ratio
                img = img.resize((self.MAP_WIDTH, self.MAP_HEIGHT), Image.Resampling.LANCZOS)
                logger.info(f"Successfully fetched satellite imagery: {img.size}")

                # Save to cache
                try:
                    Config.CACHE_PATH.mkdir(parents=True, exist_ok=True)
                    # Convert to RGB before saving as JPEG (JPEG doesn't support RGBA or palette mode)
                    cache_img = img.convert("RGB")
                    cache_img.save(cache_file, "JPEG", quality=95)
                    logger.info(f"Cached satellite imagery to {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to cache image: {e}")

                return img
            else:
                logger.warning(f"Failed to fetch satellite map: {response.status_code}")
                return None

        except Exception as e:
            logger.warning(f"Error fetching satellite map: {e}")
            return None

    def _latlon_to_pixel_mercator(self, lat: float, lon: float, zoom: int = 11) -> Tuple[int, int]:
        """
        Convert lat/lon to pixel coordinates using Web Mercator projection (EPSG:3857).
        This matches Google Maps' projection.

        Args:
            lat: Latitude
            lon: Longitude
            zoom: Zoom level (must match Google Maps request)

        Returns:
            Tuple of (x, y) pixel coordinates
        """
        import math

        # Web Mercator projection
        # Convert to tile coordinates at given zoom level
        lat_rad = math.radians(lat)
        n = 2.0**zoom

        x_tile = (lon + 180.0) / 360.0 * n
        y_tile = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n

        # Convert center point to tile coordinates
        center_lat_rad = math.radians(self.CENTER_LAT)
        x_center_tile = (self.CENTER_LON + 180.0) / 360.0 * n
        y_center_tile = (1.0 - math.asinh(math.tan(center_lat_rad)) / math.pi) / 2.0 * n

        # Calculate offset from center in tiles
        x_offset = x_tile - x_center_tile
        y_offset = y_tile - y_center_tile

        # Convert to pixels (256 pixels per tile at scale=1, 512 at scale=2)
        # At zoom 9 with scale=2, we get 1280x720 image
        # Center of image is at (640, 360) in the 1280x720 source
        # After scaling to 4K, center is at (1920, 1080)

        pixels_per_tile = 512  # scale=2
        x_pixel_offset = x_offset * pixels_per_tile
        y_pixel_offset = y_offset * pixels_per_tile

        # Scale to 4K (1280x720 -> 3840x2160)
        scale_factor = self.MAP_WIDTH / 1280.0

        x = int(self.MAP_WIDTH / 2 + x_pixel_offset * scale_factor)
        y = int(self.MAP_HEIGHT / 2 + y_pixel_offset * scale_factor)

        return (x, y)

    def render_full_map(self, vessels: List[FerryVessel]) -> Image.Image:
        """
        Render full-screen ferry map with vessel positions.

        Args:
            vessels: List of all ferry vessels to plot

        Returns:
            Full 4K map image
        """
        # Try to fetch satellite background
        img = self._fetch_satellite_map()

        if img is None:
            # Fallback to solid blue background
            img = Image.new("RGB", (self.MAP_WIDTH, self.MAP_HEIGHT), self.WATER_COLOR)

        # Create semi-transparent overlay for drawing
        overlay = Image.new("RGBA", (self.MAP_WIDTH, self.MAP_HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        # Draw semi-transparent header background
        draw.rectangle([0, 0, self.MAP_WIDTH, 280], fill=(0, 0, 0, 180))

        # Composite overlay onto image
        img = img.convert("RGBA")
        img = Image.alpha_composite(img, overlay)
        draw = ImageDraw.Draw(img)

        # Draw title
        title = "Washington State Ferries - Live Vessel Positions"
        title_bbox = draw.textbbox((0, 0), title, font=self.title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(
            ((self.MAP_WIDTH - title_width) // 2, 50),
            title,
            fill=self.TEXT_COLOR,
            font=self.title_font,
        )

        # Draw timestamp
        timestamp = datetime.now().strftime("%I:%M %p %Z").lstrip("0")
        ts_bbox = draw.textbbox((0, 0), timestamp, font=self.label_font)
        ts_width = ts_bbox[2] - ts_bbox[0]
        draw.text(
            ((self.MAP_WIDTH - ts_width) // 2, 200),
            timestamp,
            fill=self.TEXT_COLOR,
            font=self.label_font,
        )

        # Draw vessels
        # Track positions to avoid label overlap
        drawn_positions = []
        for vessel in vessels:
            if vessel.latitude and vessel.longitude:
                pos = self._latlon_to_pixel_mercator(vessel.latitude, vessel.longitude)
                if self._is_valid_position(pos):
                    self._draw_vessel(draw, pos, vessel, drawn_positions)
                    drawn_positions.append(pos)

        # Draw legend
        self._draw_legend(draw)

        # Draw vessel count
        count_text = f"{len(vessels)} vessels in service"
        draw.text(
            (self.MARGIN, self.MAP_HEIGHT - 150),
            count_text,
            fill=self.TEXT_COLOR,
            font=self.label_font,
        )

        # Convert back to RGB for JPEG output
        img = img.convert("RGB")

        logger.info(f"Rendered ferry map with {len(vessels)} vessel(s)")
        return img

    def _latlon_to_pixel(self, lat: float, lon: float) -> Tuple[int, int]:
        """
        Convert lat/lon to pixel coordinates.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Tuple of (x, y) pixel coordinates
        """
        # Normalize to 0-1 range
        x_norm = (lon - self.MIN_LON) / (self.MAX_LON - self.MIN_LON)
        y_norm = (lat - self.MIN_LAT) / (self.MAX_LAT - self.MIN_LAT)

        # Convert to pixel coordinates (flip y for screen coords)
        # Reserve top 300px for title/timestamp
        usable_height = self.MAP_HEIGHT - 400
        x = int(self.MARGIN + x_norm * (self.MAP_WIDTH - 2 * self.MARGIN))
        y = int(300 + (1 - y_norm) * usable_height)

        return (x, y)

    def _is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Check if position is within drawable area."""
        x, y = pos
        return (
            self.MARGIN <= x <= self.MAP_WIDTH - self.MARGIN and 300 <= y <= self.MAP_HEIGHT - 100
        )

    def _draw_vessel(
        self,
        draw: ImageDraw.ImageDraw,
        pos: Tuple[int, int],
        vessel: FerryVessel,
        drawn_positions: List[Tuple[int, int]] = None,
    ) -> None:
        """
        Draw vessel marker with heading indicator.

        Args:
            draw: ImageDraw object
            pos: (x, y) position
            vessel: Vessel data
            drawn_positions: List of already drawn positions to avoid overlap
        """
        x, y = pos
        size = 30

        # Draw circle for vessel
        draw.ellipse(
            [x - size, y - size, x + size, y + size],
            fill=self.VESSEL_COLOR,
            outline=self.TEXT_COLOR,
            width=3,
        )

        # Draw heading indicator if vessel is moving
        if vessel.speed and vessel.speed > 1:
            # Convert heading to radians (heading is degrees from north, clockwise)
            import math

            heading_rad = math.radians(vessel.heading)

            # Calculate arrow endpoint (pointing in heading direction)
            arrow_length = 50
            end_x = x + arrow_length * math.sin(heading_rad)
            end_y = y - arrow_length * math.cos(
                heading_rad
            )  # Negative because screen y is inverted

            draw.line([(x, y), (end_x, end_y)], fill=self.TEXT_COLOR, width=4)

            # Draw arrowhead
            arrow_size = 15
            left_angle = heading_rad - math.radians(140)
            right_angle = heading_rad + math.radians(140)

            left_x = end_x + arrow_size * math.sin(left_angle)
            left_y = end_y - arrow_size * math.cos(left_angle)
            right_x = end_x + arrow_size * math.sin(right_angle)
            right_y = end_y - arrow_size * math.cos(right_angle)

            draw.polygon(
                [(end_x, end_y), (left_x, left_y), (right_x, right_y)], fill=self.TEXT_COLOR
            )

        # Draw vessel name and speed
        info_text = vessel.name
        if vessel.speed:
            info_text += f" ({vessel.speed:.1f} kts)"

        bbox = draw.textbbox((0, 0), info_text, font=self.small_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Check if label would overlap with nearby vessels
        # Count how many vessels are within proximity (for cascading offsets)
        nearby_count = 0
        if drawn_positions:
            for prev_x, prev_y in drawn_positions:
                distance = ((x - prev_x) ** 2 + (y - prev_y) ** 2) ** 0.5
                # If vessels are within 100 pixels, count them
                if distance < 100:
                    nearby_count += 1

        # Calculate label position with cascading vertical offsets
        label_x = x - text_width // 2
        # Base position below the vessel marker
        base_label_y = y + size + 10
        # Each nearby vessel pushes this label down by 40 pixels
        label_y = base_label_y + (nearby_count * 40)

        # Draw text with shadow for readability
        shadow_offset = 2
        draw.text(
            (label_x + shadow_offset, label_y + shadow_offset),
            info_text,
            fill=(0, 0, 0),
            font=self.small_font,
        )
        draw.text((label_x, label_y), info_text, fill=self.TEXT_COLOR, font=self.small_font)

    def _draw_legend(self, draw: ImageDraw.ImageDraw) -> None:
        """Draw map legend."""
        legend_x = self.MAP_WIDTH - 500
        legend_y = self.MAP_HEIGHT - 300

        # Legend background
        draw.rectangle(
            [legend_x - 20, legend_y - 20, legend_x + 400, legend_y + 200],
            fill=(0, 0, 0, 180),
            outline=self.TEXT_COLOR,
            width=2,
        )

        # Legend title
        draw.text((legend_x, legend_y), "LEGEND", fill=self.TEXT_COLOR, font=self.label_font)

        # Vessel indicator
        draw.ellipse(
            [legend_x, legend_y + 70, legend_x + 30, legend_y + 100],
            fill=self.VESSEL_COLOR,
            outline=self.TEXT_COLOR,
            width=2,
        )
        draw.text(
            (legend_x + 50, legend_y + 70),
            "Ferry Vessel",
            fill=self.TEXT_COLOR,
            font=self.small_font,
        )

        # Moving vessel indicator
        draw.line(
            [(legend_x + 15, legend_y + 140), (legend_x + 15, legend_y + 100)],
            fill=self.TEXT_COLOR,
            width=3,
        )
        draw.text(
            (legend_x + 50, legend_y + 125),
            "Heading (if moving)",
            fill=self.TEXT_COLOR,
            font=self.small_font,
        )
