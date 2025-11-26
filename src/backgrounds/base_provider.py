"""
Base class for background image providers.
"""

from abc import ABC, abstractmethod
from typing import Optional

from PIL import Image


class BackgroundProvider(ABC):
    """
    Abstract base class for background image providers.
    All providers must implement get_background().
    """

    @abstractmethod
    def get_background(self, query: str, width: int, height: int) -> Optional[Image.Image]:
        """
        Get background image matching query at specified dimensions.

        Args:
            query: Search query or path identifier
            width: Target width in pixels
            height: Target height in pixels

        Returns:
            PIL Image at exact dimensions, or None on failure
        """
        pass
