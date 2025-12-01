"""
Text layout engines for different display styles.
Each layout creates a unique visual aesthetic for optimal readability.
"""

import logging
from abc import ABC, abstractmethod

from PIL import ImageDraw, ImageFont

from src.config import Config

logger = logging.getLogger(__name__)


class TextLayout(ABC):
    """
    Base class for text layout engines.
    Handles safe zone calculations and font management.
    """

    def __init__(
        self,
        font_title: ImageFont.FreeTypeFont,
        font_body: ImageFont.FreeTypeFont,
        font_small: ImageFont.FreeTypeFont,
    ):
        """
        Initialize layout with fonts.

        Args:
            font_title: Large font for titles
            font_body: Medium font for body text
            font_small: Small font for details
        """
        self.font_title = font_title
        self.font_body = font_body
        self.font_small = font_small

        # Calculate safe zone bounds
        self.safe_left = Config.SAFE_MARGIN_H
        self.safe_top = Config.SAFE_MARGIN_V
        self.safe_right = Config.IMAGE_WIDTH - Config.SAFE_MARGIN_H
        self.safe_bottom = Config.IMAGE_HEIGHT - Config.SAFE_MARGIN_V
        self.safe_width = self.safe_right - self.safe_left
        self.safe_height = self.safe_bottom - self.safe_top

    @abstractmethod
    def draw_content(self, draw: ImageDraw.ImageDraw, lines: list[str]) -> None:
        """
        Draw text content using this layout style.

        Args:
            draw: PIL ImageDraw object
            lines: List of text lines to render
        """
        pass


class CenteredLayout(TextLayout):
    """
    Centered layout with generous spacing.
    Perfect for simple, impactful displays like weather and stock quotes.
    """

    def draw_content(self, draw: ImageDraw.ImageDraw, lines: list[str]) -> None:
        """Draw centered text with 220px line spacing."""
        y = self.safe_top + 300  # Start below top margin

        for line in lines:
            # Calculate text width for centering
            bbox = draw.textbbox((0, 0), line, font=self.font_body)
            text_width = bbox[2] - bbox[0]
            x = (Config.IMAGE_WIDTH - text_width) / 2

            # Draw text
            draw.text((x, y), line, fill=(255, 255, 255), font=self.font_body)
            y += 220  # Generous spacing


class LeftAlignedLayout(TextLayout):
    """
    Left-aligned layout with smart indentation detection.
    Ideal for lists, sports fixtures, and whale sightings.
    """

    def draw_content(self, draw: ImageDraw.ImageDraw, lines: list[str]) -> None:
        """Draw left-aligned text with 150px line spacing and indentation support."""
        y = self.safe_top + 200

        for line in lines:
            # Detect indentation (lines starting with spaces)
            indent = 0
            if line.startswith("  "):
                indent = 100  # Indent for sub-items

            x = self.safe_left + indent

            # Draw text
            draw.text((x, y), line, fill=(255, 255, 255), font=self.font_body)
            y += 150


class GridLayout(TextLayout):
    """
    Compact grid layout for tabular data.
    Perfect for league tables and dense information.
    """

    def draw_content(self, draw: ImageDraw.ImageDraw, lines: list[str]) -> None:
        """Draw compact grid layout with 100px spacing."""
        y = self.safe_top + 150

        for line in lines:
            x = self.safe_left

            # Use smaller font for dense data
            draw.text((x, y), line, fill=(255, 255, 255), font=self.font_small)
            y += 100  # Tight spacing for tables


class SplitLayout(TextLayout):
    """
    Split layout: text on left half, reserved space on right for map/image.
    Used for ferry schedules with vessel map overlay.
    """

    def draw_content(self, draw: ImageDraw.ImageDraw, lines: list[str]) -> None:
        """Draw text confined to left half of image."""
        y = self.safe_top + 200

        # Constrain text to left half
        # max_x = Config.IMAGE_WIDTH // 2 - Config.SAFE_MARGIN_H  # Reserved for text wrapping

        for line in lines:
            x = self.safe_left

            # Draw text (will be clipped if too long)
            draw.text((x, y), line, fill=(255, 255, 255), font=self.font_body)
            y += 180


class WeatherLayout(TextLayout):
    """
    Custom weather layout with mixed fonts and tight spacing.
    Title (small) -> Temp (huge) -> Description (medium) -> Details table (small).
    """

    def draw_content(self, draw: ImageDraw.ImageDraw, lines: list[str]) -> None:
        """Draw weather with custom spacing and font sizes."""
        y = self.safe_top + 250

        for i, line in enumerate(lines):
            if not line.strip():  # Skip empty lines
                continue

            # Line 0: City name (title font, centered)
            if i == 0:
                bbox = draw.textbbox((0, 0), line, font=self.font_title)
                text_width = bbox[2] - bbox[0]
                x = (Config.IMAGE_WIDTH - text_width) / 2
                draw.text((x, y), line, fill=(255, 255, 255), font=self.font_title)
                y += 150  # Reduced spacing after title

            # Line 1: Temperature (body font, centered)
            elif i == 1:
                bbox = draw.textbbox((0, 0), line, font=self.font_body)
                text_width = bbox[2] - bbox[0]
                x = (Config.IMAGE_WIDTH - text_width) / 2
                draw.text((x, y), line, fill=(255, 255, 255), font=self.font_body)
                y += 200  # Normal spacing after temp

            # Line 2: Description (body font, centered)
            elif i == 2:
                bbox = draw.textbbox((0, 0), line, font=self.font_body)
                text_width = bbox[2] - bbox[0]
                x = (Config.IMAGE_WIDTH - text_width) / 2
                draw.text((x, y), line, fill=(255, 255, 255), font=self.font_body)
                y += 120  # Reduced spacing before details

            # Lines 3+: Details table (small font, centered)
            else:
                bbox = draw.textbbox((0, 0), line, font=self.font_small)
                text_width = bbox[2] - bbox[0]
                x = (Config.IMAGE_WIDTH - text_width) / 2
                draw.text((x, y), line, fill=(255, 255, 255), font=self.font_small)
                y += 100  # Tight spacing for table rows


class LayoutFactory:
    """
    Factory for creating text layout instances.
    """

    _layouts = {
        "centered": CenteredLayout,
        "left": LeftAlignedLayout,
        "grid": GridLayout,
        "split": SplitLayout,
        "weather": WeatherLayout,
    }

    @classmethod
    def get_layout(
        cls,
        layout_type: str,
        font_title: ImageFont.FreeTypeFont,
        font_body: ImageFont.FreeTypeFont,
        font_small: ImageFont.FreeTypeFont,
    ) -> TextLayout:
        """
        Get layout instance for type.

        Args:
            layout_type: Layout type name
            font_title: Title font
            font_body: Body font
            font_small: Small font

        Returns:
            Layout instance (defaults to centered if type unknown)
        """
        layout_class = cls._layouts.get(layout_type.lower(), CenteredLayout)
        return layout_class(font_title, font_body, font_small)  # type: ignore[abstract]  # Factory creates concrete subclasses
