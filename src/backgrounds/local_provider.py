"""
Local file background provider.
Loads and crops images from local filesystem.
"""

import logging
import random
from pathlib import Path
from typing import List, Optional

from PIL import Image

from src.backgrounds.base_provider import BackgroundProvider
from src.config import Config
from src.utils.image_utils import smart_crop_to_fill

logger = logging.getLogger(__name__)


class LocalProvider(BackgroundProvider):
    """
    Provides background images from local filesystem.
    Expects directory structure: backgrounds/topic/category/
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize local provider.

        Args:
            base_path: Base directory for backgrounds (default: Config.BACKGROUNDS_PATH)
        """
        self.base_path = base_path or Config.BACKGROUNDS_PATH

    def get_background(self, query: str, width: int, height: int) -> Optional[Image.Image]:
        """
        Load random background from local directory.

        Args:
            query: Path relative to base (e.g., 'weather/sunny' or 'tesla')
            width: Target width
            height: Target height

        Returns:
            Cropped and resized image, or None if no images found
        """
        # Construct directory path
        bg_dir = self.base_path / query

        if not bg_dir.exists():
            logger.warning(f"Background directory not found: {bg_dir}")
            return None

        # Find all image files
        image_files = self._find_images(bg_dir)

        if not image_files:
            logger.warning(f"No images found in {bg_dir}")
            return None

        # Select random image
        selected = random.choice(image_files)

        try:
            img = Image.open(selected)

            # Crop and resize to exact dimensions
            img = smart_crop_to_fill(img, width, height)

            logger.debug(f"Loaded background: {selected.name}")
            return img

        except Exception as e:
            logger.error(f"Failed to load background {selected}: {e}")
            return None

    def _find_images(self, directory: Path) -> List[Path]:
        """
        Find all image files in directory (non-recursive).

        Args:
            directory: Directory to search

        Returns:
            List of image file paths
        """
        extensions = [".jpg", ".jpeg", ".png"]
        images = []

        for ext in extensions:
            images.extend(directory.glob(f"*{ext}"))
            images.extend(directory.glob(f"*{ext.upper()}"))

        return images
