"""
Main image renderer for signage content.
Coordinates backgrounds, layouts, and text rendering.
Supports both PIL and HTML rendering modes.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Any

from PIL import Image, ImageDraw, ImageFont

from src.backgrounds import BackgroundFactory
from src.config import Config
from src.models.signage_data import SignageContent, AmbientWeatherData
from src.renderers.text_layouts import LayoutFactory
from src.utils.image_utils import add_text_overlay, ensure_exact_size
from src.utils.output_manager import OutputManager
from src.utils.template_renderer import TemplateRenderer
from src.utils.html_renderer import SyncHTMLRenderer
from src.utils.logging_utils import timeit

logger = logging.getLogger(__name__)


class SignageRenderer:
    """
    Main renderer for signage images.
    Produces aesthetically pleasing 4K images with proper composition.
    Supports both PIL (legacy) and HTML (modern) rendering modes.
    """
    
    def __init__(self, use_html: bool = False, output_manager: Optional[OutputManager] = None):
        """
        Initialize renderer and load fonts.
        
        Args:
            use_html: Use HTML rendering instead of PIL (default: False for backward compatibility)
            output_manager: OutputManager instance for multi-resolution saves (creates default if None)
        """
        self.width = Config.IMAGE_WIDTH
        self.height = Config.IMAGE_HEIGHT
        self.use_html = use_html
        
        # Initialize output manager
        self.output_manager = output_manager or OutputManager()
        
        # Load fonts with fallback (for PIL mode)
        self.font_title = self._load_font(Config.FONT_PATH, 180)
        self.font_body = self._load_font(Config.FONT_PATH, 120)
        self.font_small = self._load_font(Config.FONT_PATH, 80)
        
        # Initialize HTML rendering components if needed
        if self.use_html:
            self.template_renderer = TemplateRenderer()
            self.html_renderer = SyncHTMLRenderer()
            logger.info("SignageRenderer initialized in HTML mode")
        else:
            logger.info("SignageRenderer initialized in PIL mode")
    
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
    
    @timeit
    def render(
        self,
        content: SignageContent,
        filename: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        weather_data: Optional[AmbientWeatherData] = None,
        ferry_data: Optional[Any] = None,
        stock_data: Optional[Any] = None,
        speedtest_data: Optional[Any] = None,
        sensors_data: Optional[Any] = None,
        sports_data: Optional[Any] = None
    ) -> List[Path]:
        """
        Render signage content to image file(s).
        
        Args:
            content: SignageContent to render
            filename: Output filename (defaults to content.filename_prefix + timestamp)
            timestamp: Timestamp for footer (defaults to content.timestamp or now)
            weather_data: Optional weather data for card-based rendering
            ferry_data: Optional ferry data for schedule rendering
            stock_data: Optional stock data for quote rendering
            speedtest_data: Optional speedtest data for results rendering
            sensors_data: Optional sensor data for sensors display
            sports_data: Optional sports data for football/sports display
        
        Returns:
            List of paths where image was saved (one per output profile)
        """
        # Generate filename if not provided
        if filename is None:
            if timestamp is None:
                timestamp = content.timestamp or Config.get_current_time()
            timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
            filename = f"{content.filename_prefix}_{timestamp_str}.png"
        
        # Set timestamp default
        if timestamp is None:
            timestamp = content.timestamp or Config.get_current_time()
        
        # Choose rendering path
        if self.use_html:
            return self._render_html(content, filename, timestamp, weather_data, ferry_data, stock_data, speedtest_data, sensors_data, sports_data)
        else:
            return self._render_pil(content, filename, timestamp, weather_data)
    
    def _render_pil(
        self,
        content: SignageContent,
        filename: str,
        timestamp: datetime,
        weather_data: Optional[AmbientWeatherData] = None
    ) -> List[Path]:
        """
        Render using PIL (legacy mode).
        
        Returns:
            List of paths where image was saved
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
        
        # Step 2: Check if we should use card-based weather renderer
        if content.layout_type == "weather_cards" and weather_data:
            from src.renderers.weather_card_renderer import WeatherCardRenderer
            
            # Add light overlay for readability
            img = add_text_overlay(img, opacity=0.3)
            
            # Render weather cards
            card_renderer = WeatherCardRenderer()
            img = card_renderer.render(weather_data, img)
            
            # Save and return
            output_path.parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, "JPEG", quality=95)
            logger.info(f"Saved: {output_path}")
            return output_path
        
        # Standard text-based rendering
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
        
        # Step 7: Save using OutputManager for multi-resolution support
        saved_paths = self.output_manager.save_image(
            img,
            filename,
            source=content.filename_prefix
        )
        
        return saved_paths
    
    @timeit
    def _render_html(
        self,
        content: SignageContent,
        filename: str,
        timestamp: datetime,
        weather_data: Optional[AmbientWeatherData] = None,
        ferry_data: Optional[Any] = None,
        stock_data: Optional[Any] = None,
        speedtest_data: Optional[Any] = None,
        sensors_data: Optional[Any] = None,
        sports_data: Optional[Any] = None
    ) -> List[Path]:
        """
        Render using HTML templates (modern mode).
        
        Returns:
            List of paths where image was saved
        """
        logger.info(
            f"Rendering {content.filename_prefix} with HTML: "
            f"{content.layout_type} layout, {content.background_mode} background"
        )
        
        # Step 1: Get background image
        bg_img = self._get_background_image(
            content.background_mode,
            content.background_query
        )
        
        # Step 2: Check if we should use weather cards template
        if content.layout_type == "weather_cards" and weather_data:
            html = self.template_renderer.render_weather_cards(weather_data)
        elif content.layout_type == "modern_ambient" and weather_data:
            html = self.template_renderer.render_ambient_dashboard(weather_data)
        elif content.layout_type == "modern_ferry" and ferry_data:
            html = self.template_renderer.render_ferry_schedule(ferry_data)
        elif content.layout_type == "modern_stock" and stock_data:
            html = self.template_renderer.render_stock_quote(stock_data)
        elif content.layout_type == "modern_speedtest" and speedtest_data:
            html = self.template_renderer.render_speedtest_results(speedtest_data)
        elif content.layout_type == "modern_sensors" and sensors_data:
            html = self.template_renderer.render_sensors_display(sensors_data)
        elif content.layout_type == "modern_football" and sports_data:
            html = self.template_renderer.render_football_display(sports_data)
        elif content.layout_type == "modern_rugby" and sports_data:
            html = self.template_renderer.render_rugby_display(sports_data)
        else:
            # Render text layout template
            html = self.template_renderer.render_layout(
                content.layout_type,
                content.lines,
                timestamp=timestamp.strftime("%m/%d %I:%M %p %Z")
            )
        
        # Step 3: Convert HTML to image
        text_img = self.html_renderer.render_html_to_image(html)
        
        # Step 4: Composite text over background
        # Add semi-transparent overlay for readability
        bg_img = add_text_overlay(bg_img, opacity=0.4)
        
        # Composite text (HTML already has transparent background)
        bg_img = bg_img.convert("RGBA")
        text_img = text_img.convert("RGBA")
        composite = Image.alpha_composite(bg_img, text_img)
        composite = composite.convert("RGB")
        
        # Step 5: Ensure exact size
        composite = ensure_exact_size(composite, self.width, self.height)
        
        # Step 6: Save using OutputManager
        saved_paths = self.output_manager.save_image(
            composite,
            filename,
            source=content.filename_prefix
        )
        
        return saved_paths
