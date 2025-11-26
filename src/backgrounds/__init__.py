"""
Background factory for managing providers.
"""

import logging
from typing import Dict, Optional, Type

from PIL import Image

from src.backgrounds.base_provider import BackgroundProvider
from src.backgrounds.gradient_provider import GradientProvider
from src.backgrounds.local_provider import LocalProvider
from src.backgrounds.pexels_provider import PexelsProvider
from src.backgrounds.unsplash_provider import UnsplashProvider

logger = logging.getLogger(__name__)


class BackgroundFactory:
    """
    Factory for background providers with fallback support.
    """

    _providers: Dict[str, Type[BackgroundProvider]] = {
        "gradient": GradientProvider,
        "local": LocalProvider,
        "unsplash": UnsplashProvider,
        "pexels": PexelsProvider,
    }

    _instances: Dict[str, BackgroundProvider] = {}

    @classmethod
    def get_provider(cls, mode: str) -> BackgroundProvider:
        """
        Get provider instance for mode.
        Providers are cached after first instantiation.

        Args:
            mode: Provider mode ('gradient', 'local', 'unsplash', 'pexels')

        Returns:
            Provider instance (falls back to gradient if mode unknown)
        """
        # Normalize mode
        mode = mode.lower()

        # Check if we have a cached instance
        if mode in cls._instances:
            return cls._instances[mode]

        # Get provider class
        provider_class = cls._providers.get(mode, GradientProvider)

        # Create and cache instance
        try:
            instance = provider_class()
            cls._instances[mode] = instance
            return instance
        except Exception as e:
            logger.error(f"Failed to create provider '{mode}': {e}")
            # Fallback to gradient
            if mode != "gradient":
                logger.warning("Falling back to gradient provider")
                return cls.get_provider("gradient")
            raise

    @classmethod
    def get_background(cls, mode: str, query: str, width: int, height: int) -> Image.Image:
        """
        Get background image with automatic fallback.

        Args:
            mode: Provider mode
            query: Search query or path
            width: Target width
            height: Target height

        Returns:
            Background image (guaranteed to return something via fallback)
        """
        provider = cls.get_provider(mode)

        try:
            img = provider.get_background(query, width, height)

            if img:
                return img

            # Provider returned None - fallback to gradient
            if mode != "gradient":
                logger.warning(f"Provider '{mode}' returned None, falling back to gradient")
                gradient_provider = cls.get_provider("gradient")
                return gradient_provider.get_background("", width, height)

            # Even gradient failed - this shouldn't happen
            raise RuntimeError("Gradient provider failed to generate image")

        except Exception as e:
            logger.error(f"Error getting background with '{mode}': {e}")

            # Final fallback to gradient
            if mode != "gradient":
                logger.warning("Falling back to gradient due to error")
                gradient_provider = cls.get_provider("gradient")
                return gradient_provider.get_background("", width, height)

            raise
