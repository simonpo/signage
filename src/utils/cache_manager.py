"""
Cache management for downloaded images and API responses.
Prevents redundant downloads and API calls.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from src.config import Config

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Manages cached images with expiration.
    Uses MD5 hashing for cache keys.
    """

    def __init__(self, cache_path: Optional[Path] = None):
        """
        Initialize cache manager.

        Args:
            cache_path: Directory for cached files (default: Config.CACHE_PATH)
        """
        self.cache_path = cache_path or Config.CACHE_PATH
        self.cache_path.mkdir(parents=True, exist_ok=True)

    def get_cache_key(self, url_or_query: str) -> str:
        """
        Generate cache key from URL or search query.

        Args:
            url_or_query: URL or search query string

        Returns:
            MD5 hash of the input
        """
        return hashlib.md5(url_or_query.encode()).hexdigest()

    def get_cached_image(self, key: str, max_age_days: int = 7) -> Optional[Path]:
        """
        Retrieve cached image if it exists and is not too old.

        Args:
            key: Cache key (from get_cache_key)
            max_age_days: Maximum age in days

        Returns:
            Path to cached file if valid, None otherwise
        """
        cache_file = self.cache_path / f"{key}.jpg"

        if not cache_file.exists():
            return None

        # Check age
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age = datetime.now() - file_time

        if age > timedelta(days=max_age_days):
            logger.debug(f"Cache expired for key {key} (age: {age.days} days)")
            return None

        logger.debug(f"Cache hit for key {key}")
        return cache_file

    def save_to_cache(self, key: str, image_data: bytes) -> Path:
        """
        Save image data to cache.

        Args:
            key: Cache key
            image_data: Raw image bytes

        Returns:
            Path to saved cache file
        """
        cache_file = self.cache_path / f"{key}.jpg"

        cache_file.write_bytes(image_data)
        logger.debug(f"Saved to cache: {key}")

        return cache_file

    def clear_cache(self, older_than_days: int = 30) -> int:
        """
        Delete cache files older than specified days.

        Args:
            older_than_days: Delete files older than this many days

        Returns:
            Number of files deleted
        """
        cutoff_time = datetime.now() - timedelta(days=older_than_days)
        deleted_count = 0

        for cache_file in self.cache_path.glob("*.jpg"):
            try:
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)

                if file_time < cutoff_time:
                    cache_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted old cache file: {cache_file.name}")

            except OSError as e:
                logger.warning(f"Error deleting cache file {cache_file}: {e}")

        if deleted_count > 0:
            logger.info(
                f"Cleared {deleted_count} cache file(s) older than " f"{older_than_days} days"
            )

        return deleted_count
