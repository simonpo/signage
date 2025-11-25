"""
Main image renderer for signage content.
Coordinates backgrounds, layouts, and text rendering.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from src.backgrounds import BackgroundFactory
from src.config import Config
from src.models.signage_data import SignageContent
from src.renderers.text_layouts import LayoutFactory
from src.utils.image_utils import add_text_overlay, ensure_exact_size

logger = logging.getLogger(__name__)


class SignageRenderer:
    """
    Main renderer for signage images.
    Produces aesthetically pleasing 4K images with proper composition.
    """
    
    def __init__(self):
        """Initialize renderer and load fonts."""
        self.width = Config.IMAGE_WIDTH
        self.height = Config.IMAGE_HEIGHT
        
        # Load fonts with fallback
        self.font_title = self._load_font(Config.FONT_PATH, 180)
        self.font_body = self._load_font(Config.FONT_PATH, 120)
        self.font_small = self._load_font(Config.FONT_PATH, 80)
    
    def _load_font(self, path: str, size: int) -> ImageFont.FreeTypeFont:
        """
        Load font with fallback to default.
        
        Args:
            path: Font file path
            size: Font size in points
        
        Returns:
            Font object
        """
        try:
            font = ImageFont.truetype(path, size)
            logger.debug(f"Loaded font: {path} at {size}pt")
            return font
        except Exception as e:
            logger.warning(f"Failed to load font {path}: {e}. Using default.")
            return ImageFont.load_default()
    
    def _get_background_image(
        self,
        bg_mode: str,
        bg_query: Optional[str]
    ) -> Image.Image:
        """
        Get background image from appropriate provider.
        
        Args:
            bg_mode: Background mode (gradient, local, unsplash, pexels)
            bg_query: Query string or path
        
        Returns:
            Background image at exact dimensions
        """
        query = bg_query or ""
        
        img = BackgroundFactory.get_background(
            mode=bg_mode,
            query=query,
            width=self.width,
            height=self.height
        )
        
        # Paranoid check: ensure exact size
        img = ensure_exact_size(img, self.width, self.height)
        
        return img
    
    def _add_timestamp(
        self,
        draw: ImageDraw.ImageDraw,
        timestamp: datetime
    ) -> None:
        """
        Add timestamp at bottom center in safe zone.
        
        Args:
            draw: ImageDraw object
            timestamp: Timestamp to display
        """
        ts_text = f"Updated: {timestamp.strftime('%m/%d %I:%M %p %Z')}"
        
        # Calculate centered position
        bbox = draw.textbbox((0, 0), ts_text, font=self.font_small)
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) / 2
        y = self.height - Config.SAFE_MARGIN_V - 100  # 100px from safe bottom
        
        # Draw with subtle color
        draw.text((x, y), ts_text, fill=(200, 200, 255), font=self.font_small)
    
    def render(
        self,
        content: SignageContent,
        output_path: Path,
        timestamp: Optional[datetime] = None
    ) -> Path:
        """
        Render signage content to image file.
        
        Args:
            content: SignageContent to render
            output_path: Output file path
            timestamp: Timestamp for footer (defaults to content.timestamp or now)
        
        Returns:
            Path to saved image file
        """
        if timestamp is None:
            timestamp = content.timestamp or Config.get_current_time()
        
        logger.info(
            f"Rendering {content.filename_prefix} with "
            f"{content.layout_type} layout, {content.background_mode} background"
        )
        
        # Step 1: Get background image
        img = self._get_background_image(
            content.background_mode,
            content.background_query
        )
        
        # Step 2: Add semi-transparent overlay for text readability
        img = add_text_overlay(img, opacity=0.4)
        
        # Step 3: Convert to RGBA for drawing (then back to RGB for JPEG)
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        draw = ImageDraw.Draw(img)
        
        # Step 4: Get layout engine and draw content
        layout = LayoutFactory.get_layout(
            content.layout_type,
            self.font_title,
            self.font_body,
            self.font_small
        )
        
        layout.draw_content(draw, content.lines)
        
        # Step 5: Add timestamp
        self._add_timestamp(draw, timestamp)
        
        # Step 6: Paranoid dimension check
        img = ensure_exact_size(img, self.width, self.height)
        
        # Step 7: Save as high-quality JPEG
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "JPEG", quality=95)
        
        logger.info(f"Saved: {output_path}")
        return output_path
