"""
Output manager for multi-resolution rendering and device-specific archival.
Handles saving rendered images to multiple output profiles with automatic cleanup.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from PIL import Image

from src.config import Config

logger = logging.getLogger(__name__)


class OutputProfile:
    """Represents a single output profile for a device."""

    def __init__(self, name: str, width: int, height: int, output_dir: str):
        """
        Initialize output profile.

        Args:
            name: Profile name (e.g., "living_room_4k")
            width: Target width in pixels
            height: Target height in pixels
            output_dir: Output directory path for this profile
        """
        self.name = name
        self.width = width
        self.height = height
        self.output_dir = Path(output_dir)
        self.archive_dir = self.output_dir / "archive"

        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        return f"OutputProfile({self.name}, {self.width}x{self.height})"


class OutputManager:
    """
    Manages multi-resolution output rendering and archival.

    Parses OUTPUT_PROFILES from environment, handles device-specific
    directories, and maintains archive with configurable retention.
    """

    def __init__(self):
        """Initialize output manager with profiles from config."""
        self.profiles = self._parse_profiles()
        self.archive_keep_count = Config.ARCHIVE_KEEP_COUNT

        if not self.profiles:
            logger.warning("No output profiles configured, using default profile")
            self.profiles = [self._get_default_profile()]

        logger.info(f"Initialized OutputManager with {len(self.profiles)} profile(s)")
        for profile in self.profiles:
            logger.info(f"  - {profile}")

    def _parse_profiles(self) -> list[OutputProfile]:
        """
        Parse OUTPUT_PROFILES from environment.

        Expected format (JSON):
        [
            {"name": "living_room_4k", "width": 3840, "height": 2160, "output_dir": "art_folder/living_room"},
            {"name": "bedroom_hd", "width": 1920, "height": 1080, "output_dir": "art_folder/bedroom"}
        ]

        Returns:
            List of OutputProfile objects
        """
        profiles_json = Config.OUTPUT_PROFILES

        if not profiles_json or profiles_json.strip() == "":
            return []

        try:
            profiles_data = json.loads(profiles_json)

            if not isinstance(profiles_data, list):
                logger.error("OUTPUT_PROFILES must be a JSON array")
                return []

            profiles = []
            for profile_data in profiles_data:
                try:
                    profile = OutputProfile(
                        name=profile_data["name"],
                        width=int(profile_data["width"]),
                        height=int(profile_data["height"]),
                        output_dir=profile_data["output_dir"],
                    )
                    profiles.append(profile)
                except (KeyError, ValueError, TypeError) as e:
                    logger.error(f"Invalid profile data: {profile_data} - {e}")
                    continue

            return profiles

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OUTPUT_PROFILES JSON: {e}")
            return []

    def _get_default_profile(self) -> OutputProfile:
        """
        Get default output profile using existing OUTPUT_DIR.

        Returns:
            Default OutputProfile with 4K resolution
        """
        return OutputProfile(
            name="default",
            width=Config.IMAGE_WIDTH,
            height=Config.IMAGE_HEIGHT,
            output_dir=str(Config.OUTPUT_PATH),
        )

    def save_image(
        self, image: Image.Image, filename: str, source: Optional[str] = None
    ) -> list[Path]:
        """
        Save image to all configured output profiles.

        Args:
            image: PIL Image to save (should be at highest resolution)
            filename: Base filename (e.g., "weather.png")
            source: Optional source identifier for logging

        Returns:
            List of paths where image was saved
        """
        saved_paths = []
        source_info = f" [{source}]" if source else ""

        logger.info(f"Saving image{source_info}: {filename}")

        for profile in self.profiles:
            try:
                # Resize image if needed
                if image.width != profile.width or image.height != profile.height:

                    logger.debug(
                        f"Resizing from {image.width}x{image.height} to "
                        f"{profile.width}x{profile.height} for {profile.name}"
                    )
                    resized = image.resize(
                        (profile.width, profile.height), Image.Resampling.LANCZOS
                    )
                else:
                    resized = image

                # Archive old file before overwriting (if it exists)
                output_path = profile.output_dir / filename
                self._archive_old_file(profile, filename)

                # Save to output directory
                resized.save(output_path, "PNG", optimize=True)
                saved_paths.append(output_path)

                logger.info(
                    f"Saved to {profile.name}: {output_path} "
                    f"({output_path.stat().st_size / 1024:.1f} KB)"
                )

            except Exception as e:
                logger.error(f"Failed to save image to {profile.name}: {e}", exc_info=True)

        return saved_paths

    def _archive_old_file(self, profile: OutputProfile, filename: str) -> None:
        """
        Archive the old version of a file before overwriting.

        Args:
            profile: Output profile
            filename: Filename being replaced
        """
        old_file = profile.output_dir / filename

        if not old_file.exists():
            return

        # Create timestamped archive filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = old_file.stem
        archive_name = f"{base_name}_{timestamp}.png"
        archive_path = profile.archive_dir / archive_name

        try:
            # Move to archive
            shutil.move(str(old_file), str(archive_path))
            logger.debug(f"Archived {filename} to {archive_path}")

            # Clean up old archives
            self._cleanup_archives(profile, base_name)

        except Exception as e:
            logger.warning(f"Failed to archive {old_file}: {e}")

    def _cleanup_archives(self, profile: OutputProfile, base_name: str) -> None:
        """
        Remove old archived files beyond ARCHIVE_KEEP_COUNT.

        Args:
            profile: Output profile
            base_name: Base filename (without timestamp and extension)
        """
        if self.archive_keep_count <= 0:
            return

        # Find all archives for this base filename
        pattern = f"{base_name}_*.png"
        archives = sorted(
            profile.archive_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True
        )

        # Remove old archives beyond keep count
        for old_archive in archives[self.archive_keep_count :]:
            try:
                old_archive.unlink()
                logger.debug(f"Deleted old archive: {old_archive}")
            except Exception as e:
                logger.warning(f"Failed to delete {old_archive}: {e}")

    def get_primary_output_dir(self) -> Path:
        """
        Get the primary output directory (first profile or default).

        Returns:
            Path to primary output directory
        """
        return self.profiles[0].output_dir

    def get_all_output_dirs(self) -> list[Path]:
        """
        Get all output directories.

        Returns:
            List of all output directory paths
        """
        return [profile.output_dir for profile in self.profiles]

    def cleanup_old_files(self, days: int) -> None:
        """
        Remove files older than specified days from all output directories.

        Args:
            days: Number of days to keep files
        """

        cutoff_time = datetime.now().timestamp() - (days * 86400)

        logger.info(f"Cleaning up files older than {days} days")

        for profile in self.profiles:
            deleted_count = 0

            # Clean output directory
            for file_path in profile.output_dir.glob("*.png"):
                if file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {file_path}: {e}")

            # Clean archive directory
            for file_path in profile.archive_dir.glob("*.png"):
                if file_path.stat().st_mtime < cutoff_time:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old archive: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to delete {file_path}: {e}")

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old file(s) from {profile.name}")
