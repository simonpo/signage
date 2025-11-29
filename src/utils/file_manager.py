"""
File management for signage images.
Handles date-based filenames and cleanup of old files.
"""

import logging
import re
from datetime import datetime, timedelta
from pathlib import Path

from src.config import Config

logger = logging.getLogger(__name__)


class FileManager:
    """
    Manages signage image files with date-based naming.
    Format: prefix_YYYY-MM-DD.jpg
    """

    # Regex to parse date from filename: prefix_YYYY-MM-DD.jpg
    FILENAME_PATTERN = re.compile(r"^(.+?)_(\d{4}-\d{2}-\d{2})\.jpg$")

    def __init__(self, output_path: Path | None = None, keep_days: int | None = None):
        """
        Initialize file manager.

        Args:
            output_path: Directory for output files (default: Config.OUTPUT_PATH)
            keep_days: Days to keep old files (default: Config.KEEP_DAYS)
        """
        self.output_path = output_path or Config.OUTPUT_PATH
        self.keep_days = keep_days if keep_days is not None else Config.KEEP_DAYS
        self.output_path.mkdir(parents=True, exist_ok=True)

    def get_current_filename(self, prefix: str, date: datetime | None = None) -> str:
        """
        Generate date-based filename.

        Args:
            prefix: Filename prefix (e.g., 'tesla', 'weather')
            date: Date for filename (default: current date)

        Returns:
            Filename in format: prefix_YYYY-MM-DD.jpg
        """
        if date is None:
            date = Config.get_current_time()

        date_str = date.strftime("%Y-%m-%d")
        return f"{prefix}_{date_str}.jpg"

    def get_file_path(self, prefix: str, date: datetime | None = None) -> Path:
        """
        Get full path for a signage file.

        Args:
            prefix: Filename prefix
            date: Date for filename (default: current date)

        Returns:
            Full Path object
        """
        filename = self.get_current_filename(prefix, date)
        return self.output_path / filename

    def cleanup_old_files(self, prefix: str | None = None) -> int:
        """
        Delete files older than keep_days.

        Args:
            prefix: Only delete files with this prefix (default: all files)

        Returns:
            Number of files deleted
        """
        cutoff_date = datetime.now() - timedelta(days=self.keep_days)
        deleted_count = 0

        # Get all .jpg files in output directory
        pattern = f"{prefix}_*.jpg" if prefix else "*.jpg"

        for filepath in self.output_path.glob(pattern):
            # Parse date from filename
            match = self.FILENAME_PATTERN.match(filepath.name)
            if not match:
                # Skip files that don't match our naming pattern
                continue

            file_prefix, date_str = match.groups()

            # If prefix filter is set, check it matches
            if prefix and file_prefix != prefix:
                continue

            try:
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff_date:
                    filepath.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old file: {filepath.name}")

            except (ValueError, OSError) as e:
                logger.warning(f"Error processing {filepath.name}: {e}")
                continue

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} file(s) older than " f"{self.keep_days} days")

        return deleted_count

    def list_files(self, prefix: str | None = None) -> list[Path]:
        """
        List signage files, sorted by date (newest first).

        Args:
            prefix: Only list files with this prefix (default: all files)

        Returns:
            List of Path objects sorted by date (newest first)
        """
        pattern = f"{prefix}_*.jpg" if prefix else "*.jpg"
        files = []

        for filepath in self.output_path.glob(pattern):
            match = self.FILENAME_PATTERN.match(filepath.name)
            if match:
                files.append(filepath)

        # Sort by date in filename (newest first)
        def extract_date(path: Path) -> datetime:
            match = self.FILENAME_PATTERN.match(path.name)
            if match:
                date_str = match.group(2)
                return datetime.strptime(date_str, "%Y-%m-%d")
            return datetime.min

        return sorted(files, key=extract_date, reverse=True)

    def get_latest_file(self, prefix: str) -> Path | None:
        """
        Get the most recent file for a given prefix.

        Args:
            prefix: Filename prefix

        Returns:
            Path to most recent file, or None if no files exist
        """
        files = self.list_files(prefix)
        return files[0] if files else None
