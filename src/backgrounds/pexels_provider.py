"""
Pexels API background provider.
Fetches high-quality photos from Pexels with caching.
"""

import logging

from PIL import Image

from src.backgrounds.base_provider import BackgroundProvider
from src.clients.base import APIClient
from src.config import Config
from src.utils.cache_manager import CacheManager
from src.utils.image_utils import smart_crop_to_fill

logger = logging.getLogger(__name__)


class PexelsProvider(BackgroundProvider, APIClient):
    """
    Provides background images from Pexels API.
    Uses 7-day cache to minimize API calls.
    """

    BASE_URL = "https://api.pexels.com/v1"

    def __init__(self):
        """Initialize with Pexels API key."""
        super().__init__()

        self.api_key = Config.PEXELS_API_KEY
        self.cache = CacheManager()

        if not self.api_key:
            logger.warning("PEXELS_API_KEY not configured")

    def get_background(self, query: str, width: int, height: int) -> Image.Image | None:
        """
        Get background image from Pexels.

        Args:
            query: Search query (e.g., 'mountain landscape')
            width: Target width
            height: Target height

        Returns:
            Image at exact dimensions, or None on failure
        """
        if not self.api_key:
            logger.debug("Pexels not configured, skipping")
            return None

        # Check cache first
        cache_key = self.cache.get_cache_key(f"pexels_{query}_{width}x{height}")

        cached_path = self.cache.get_cached_image(cache_key, max_age_days=7)
        if cached_path:
            try:
                img = Image.open(cached_path)
                logger.debug(f"Loaded Pexels image from cache: {query}")
                return img
            except Exception as e:
                logger.warning(f"Failed to load cached image: {e}")

        # Search for photos
        search_url = f"{self.BASE_URL}/search"
        params = {"query": query, "orientation": "landscape", "per_page": 10}
        headers = {"Authorization": self.api_key}

        response = self._make_request(search_url, params=params, headers=headers)

        if not response:
            logger.error(f"Failed to search Pexels for '{query}'")
            return None

        try:
            data = response.json()
            photos = data.get("photos", [])

            if not photos:
                logger.warning(f"No Pexels results for '{query}'")
                return None

            # Get first photo's largest available size
            photo = photos[0]
            # Try to get original, fall back to large2x
            img_url = photo["src"].get("original") or photo["src"]["large2x"]

            # Download image
            img_response = self._make_request(img_url)

            if not img_response:
                logger.error("Failed to download Pexels image")
                return None

            # Save to cache
            self.cache.save_to_cache(cache_key, img_response.content)

            # Load and crop to exact dimensions
            from io import BytesIO

            img = Image.open(BytesIO(img_response.content))
            img = smart_crop_to_fill(img, width, height)

            logger.info(f"Fetched Pexels image: {query}")
            return img

        except (ValueError, KeyError, IndexError) as e:
            logger.error(f"Failed to process Pexels response: {e}")
            return None
