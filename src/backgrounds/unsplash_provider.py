"""
Unsplash API background provider.
Fetches high-quality photos from Unsplash with caching.
"""

import logging

from PIL import Image

from src.backgrounds.base_provider import BackgroundProvider
from src.clients.base import APIClient
from src.config import Config
from src.utils.cache_manager import CacheManager
from src.utils.image_utils import smart_crop_to_fill

logger = logging.getLogger(__name__)


class UnsplashProvider(BackgroundProvider, APIClient):
    """
    Provides background images from Unsplash API.
    Uses 7-day cache to minimize API calls.
    """

    BASE_URL = "https://api.unsplash.com"

    def __init__(self):
        """Initialize with Unsplash API key."""
        super().__init__()

        self.api_key = Config.UNSPLASH_API_KEY
        self.cache = CacheManager()

        if not self.api_key:
            logger.warning("UNSPLASH_API_KEY not configured")

    def get_background(self, query: str, width: int, height: int) -> Image.Image | None:
        """
        Get background image from Unsplash.

        Args:
            query: Search query (e.g., 'ocean sunset')
            width: Target width
            height: Target height

        Returns:
            Image at exact dimensions, or None on failure
        """
        if not self.api_key:
            logger.debug("Unsplash not configured, skipping")
            return None

        # Check cache first
        cache_key = self.cache.get_cache_key(f"unsplash_{query}_{width}x{height}")

        cached_path = self.cache.get_cached_image(cache_key, max_age_days=7)
        if cached_path:
            try:
                img = Image.open(cached_path)
                logger.debug(f"Loaded Unsplash image from cache: {query}")
                return img
            except Exception as e:
                logger.warning(f"Failed to load cached image: {e}")

        # Search for photos
        search_url = f"{self.BASE_URL}/search/photos"
        params = {"query": query, "orientation": "landscape", "per_page": 10}
        headers = {"Authorization": f"Client-ID {self.api_key}"}

        response = self._make_request(search_url, params=params, headers=headers)

        if not response:
            logger.error(f"Failed to search Unsplash for '{query}'")
            return None

        try:
            data = response.json()
            results = data.get("results", [])

            if not results:
                logger.warning(f"No Unsplash results for '{query}'")
                return None

            # Get first result's raw URL
            photo = results[0]
            raw_url = photo["urls"]["raw"]

            # Add crop parameters for efficiency
            download_url = f"{raw_url}&w={width}&h={height}&fit=crop"

            # Download image
            img_response = self._make_request(download_url)

            if not img_response:
                logger.error("Failed to download Unsplash image")
                return None

            # Save to cache
            self.cache.save_to_cache(cache_key, img_response.content)

            # Load and crop to exact dimensions
            from io import BytesIO

            img = Image.open(BytesIO(img_response.content))
            img = smart_crop_to_fill(img, width, height)

            logger.info(f"Fetched Unsplash image: {query}")
            return img

        except (ValueError, KeyError, IndexError) as e:
            logger.error(f"Failed to process Unsplash response: {e}")
            return None
