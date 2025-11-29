"""
Ferry map renderer for vessel positions.
Renders vessel locations on a simple map for split-layout ferry displays.
"""

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from src.config import Config
from src.models.signage_data import FerryVessel

logger = logging.getLogger(__name__)


class MapRenderer:
    """
    Renders ferry vessel positions on a map.
    Uses simple Mercator projection for local Puget Sound area.
    """

    # Ferry terminal coordinates (Fauntleroy - Southworth route)
    FAUNTLEROY_LAT = 47.5233
    FAUNTLEROY_LON = -122.3956
    SOUTHWORTH_LAT = 47.5114
    SOUTHWORTH_LON = -122.4967

    # Map bounds (Puget Sound area)
    MIN_LAT = 47.48
    MAX_LAT = 47.55
    MIN_LON = -122.52
    MAX_LON = -122.37

    # Map dimensions (right half of 4K image)
    MAP_WIDTH = Config.IMAGE_WIDTH // 2
    MAP_HEIGHT = Config.IMAGE_HEIGHT

    # Margins
    MARGIN = 50

    def __init__(self):
        """Initialize map renderer."""
        self.font = self._load_font()

    def _load_font(self) -> ImageFont.FreeTypeFont:
        """Load font for labels."""
        try:
            return ImageFont.truetype(Config.FONT_PATH, 40)
        except Exception:
            return ImageFont.load_default()

    def render_ferry_map(
        self, vessels: list[FerryVessel], base_map_path: Path | None = None
    ) -> Image.Image:
        """
        Render ferry map with vessel positions.

        Args:
            vessels: List of ferry vessels to plot
            base_map_path: Optional base map image (uses blue background if None)

        Returns:
            Map image at MAP_WIDTH x MAP_HEIGHT
        """
        # Create or load base map
        if base_map_path and base_map_path.exists():
            img = Image.open(base_map_path)
            img = img.resize((self.MAP_WIDTH, self.MAP_HEIGHT))
        else:
            # Create simple blue water background
            img = Image.new("RGB", (self.MAP_WIDTH, self.MAP_HEIGHT), (52, 152, 219))

        draw = ImageDraw.Draw(img)

        # Draw route line between terminals
        faunt_pos = self._latlon_to_pixel(self.FAUNTLEROY_LAT, self.FAUNTLEROY_LON)
        south_pos = self._latlon_to_pixel(self.SOUTHWORTH_LAT, self.SOUTHWORTH_LON)

        draw.line([faunt_pos, south_pos], fill=(255, 255, 255), width=5)

        # Draw terminals
        self._draw_terminal(draw, faunt_pos, "Fauntleroy")
        self._draw_terminal(draw, south_pos, "Southworth")

        # Draw vessels
        for vessel in vessels:
            pos = self._latlon_to_pixel(vessel.latitude, vessel.longitude)
            self._draw_vessel(draw, pos, vessel.name)

        logger.debug(f"Rendered ferry map with {len(vessels)} vessel(s)")
        return img

    def _latlon_to_pixel(self, lat: float, lon: float) -> tuple[int, int]:
        """
        Convert lat/lon to pixel coordinates using simple Mercator projection.

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
        x = int(self.MARGIN + x_norm * (self.MAP_WIDTH - 2 * self.MARGIN))
        y = int(self.MARGIN + (1 - y_norm) * (self.MAP_HEIGHT - 2 * self.MARGIN))

        return (x, y)

    def _draw_terminal(self, draw: ImageDraw.ImageDraw, pos: tuple[int, int], name: str) -> None:
        """
        Draw terminal marker and label.

        Args:
            draw: ImageDraw object
            pos: (x, y) position
            name: Terminal name
        """
        x, y = pos
        radius = 15

        # Draw red circle with white outline
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=(220, 53, 69),
            outline=(255, 255, 255),
            width=3,
        )

        # Draw label below marker
        bbox = draw.textbbox((0, 0), name, font=self.font)
        text_width = bbox[2] - bbox[0]
        draw.text((x - text_width // 2, y + radius + 5), name, fill=(255, 255, 255), font=self.font)

    def _draw_vessel(self, draw: ImageDraw.ImageDraw, pos: tuple[int, int], name: str) -> None:
        """
        Draw vessel marker and label.

        Args:
            draw: ImageDraw object
            pos: (x, y) position
            name: Vessel name
        """
        x, y = pos
        size = 20

        # Draw green triangle (pointing up) with white outline
        points = [
            (x, y - size),  # Top point
            (x - size // 2, y + size // 2),  # Bottom left
            (x + size // 2, y + size // 2),  # Bottom right
        ]

        draw.polygon(points, fill=(40, 167, 69), outline=(255, 255, 255))

        # Draw vessel name
        bbox = draw.textbbox((0, 0), name, font=self.font)
        text_width = bbox[2] - bbox[0]
        draw.text((x - text_width // 2, y + size + 5), name, fill=(255, 255, 255), font=self.font)
