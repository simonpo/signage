"""
Gradient background provider.
Generates beautiful gradient backgrounds programmatically.
"""

import logging

from PIL import Image, ImageDraw

from src.backgrounds.base_provider import BackgroundProvider

logger = logging.getLogger(__name__)


class GradientProvider(BackgroundProvider):
    """
    Provides gradient backgrounds.
    Generates smooth vertical gradients for clean, modern aesthetics.
    """

    def get_background(self, query: str, width: int, height: int) -> Image.Image | None:
        """
        Generate gradient background.

        Args:
            query: Ignored (gradients don't use queries)
            width: Image width
            height: Image height

        Returns:
            Image with smooth gradient from dark blue to lighter blue
        """
        # Create new RGB image
        img = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(img)

        # Define gradient colors: deep blue to light blue
        start_color = (30, 30, 80)  # Dark blue
        end_color = (130, 180, 255)  # Light blue

        # Draw vertical gradient line by line
        for y in range(height):
            # Calculate blend ratio
            ratio = y / height

            # Interpolate RGB values
            r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)

            # Draw horizontal line
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        logger.debug(f"Generated gradient background: {width}x{height}")
        return img
