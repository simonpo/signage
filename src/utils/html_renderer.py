"""
HTML-to-PNG renderer using Playwright.
Converts HTML templates to high-resolution PNG images.
"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional

from PIL import Image
from playwright.async_api import async_playwright, Browser, Page

from src.config import Config
from src.utils.logging_utils import timeit

logger = logging.getLogger(__name__)


class HTMLRenderer:
    """
    Renders HTML to PNG images using Playwright headless browser.
    Provides high-quality rendering with full CSS support.
    """
    
    def __init__(self):
        """Initialize HTML renderer."""
        self.browser: Optional[Browser] = None
        self._playwright = None
        logger.debug("HTMLRenderer initialized")
    
    async def _ensure_browser(self) -> Browser:
        """Ensure browser is running."""
        if self.browser is None:
            self._playwright = await async_playwright().start()
            self.browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    '--disable-gpu',
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-setuid-sandbox',
                ]
            )
            logger.debug("Playwright browser launched")
        
        return self.browser
    
    @timeit
    async def render_html_to_image(
        self,
        html: str,
        width: int = Config.IMAGE_WIDTH,
        height: int = Config.IMAGE_HEIGHT,
        scale: float = 1.0
    ) -> Image.Image:
        """
        Render HTML string to PIL Image.
        
        Args:
            html: HTML content to render
            width: Viewport width in pixels
            height: Viewport height in pixels
            scale: Device scale factor (1.0 = normal, 2.0 = retina)
        
        Returns:
            PIL Image object
        """
        browser = await self._ensure_browser()
        
        # Create new page with exact viewport size
        page = await browser.new_page(
            viewport={'width': width, 'height': height},
            device_scale_factor=scale
        )
        
        try:
            # Set content
            await page.set_content(html, wait_until='networkidle')
            
            # Wait for any animations/transitions
            await page.wait_for_timeout(100)
            
            # Take screenshot
            screenshot_bytes = await page.screenshot(
                type='png',
                full_page=False,
                omit_background=True  # Preserve transparent background
            )
            
            # Convert to PIL Image
            import io
            image = Image.open(io.BytesIO(screenshot_bytes))
            
            logger.debug(
                f"Rendered HTML to {image.width}x{image.height} image "
                f"({len(screenshot_bytes) / 1024:.1f} KB)"
            )
            
            return image
            
        finally:
            await page.close()
    
    @timeit
    async def render_file_to_image(
        self,
        html_file: Path,
        width: int = Config.IMAGE_WIDTH,
        height: int = Config.IMAGE_HEIGHT,
        scale: float = 1.0
    ) -> Image.Image:
        """
        Render HTML file to PIL Image.
        
        Args:
            html_file: Path to HTML file
            width: Viewport width in pixels
            height: Viewport height in pixels
            scale: Device scale factor
        
        Returns:
            PIL Image object
        """
        with open(html_file, 'r', encoding='utf-8') as f:
            html = f.read()
        
        return await self.render_html_to_image(html, width, height, scale)
    
    async def close(self):
        """Close browser and cleanup resources."""
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        
        logger.debug("HTMLRenderer closed")
    
    def __del__(self):
        """Cleanup on deletion."""
        if self.browser or self._playwright:
            # Try to close gracefully, but don't block
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.close())
                else:
                    loop.run_until_complete(self.close())
            except Exception:
                pass


class SyncHTMLRenderer:
    """
    Synchronous wrapper for HTMLRenderer.
    Provides blocking API for easier integration with existing code.
    """
    
    def __init__(self):
        """Initialize sync renderer."""
        self.renderer = HTMLRenderer()
    
    @timeit
    def render_html_to_image(
        self,
        html: str,
        width: int = Config.IMAGE_WIDTH,
        height: int = Config.IMAGE_HEIGHT,
        scale: float = 1.0
    ) -> Image.Image:
        """
        Render HTML to image (synchronous).
        
        Args:
            html: HTML content
            width: Viewport width
            height: Viewport height
            scale: Device scale factor
        
        Returns:
            PIL Image object
        """
        return asyncio.run(
            self.renderer.render_html_to_image(html, width, height, scale)
        )
    
    @timeit
    def render_file_to_image(
        self,
        html_file: Path,
        width: int = Config.IMAGE_WIDTH,
        height: int = Config.IMAGE_HEIGHT,
        scale: float = 1.0
    ) -> Image.Image:
        """
        Render HTML file to image (synchronous).
        
        Args:
            html_file: Path to HTML file
            width: Viewport width
            height: Viewport height
            scale: Device scale factor
        
        Returns:
            PIL Image object
        """
        return asyncio.run(
            self.renderer.render_file_to_image(html_file, width, height, scale)
        )
    
    def close(self):
        """Close renderer."""
        asyncio.run(self.renderer.close())
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
