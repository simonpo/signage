"""
System statistics collector for lightweight observability.
Parses logs and files to gather system health metrics.
"""

import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, TypedDict

import psutil

from src.config import Config

logger = logging.getLogger(__name__)


class GeneratorStats(TypedDict):
    """Type definition for generator statistics."""

    success: int
    failure: int
    last_run: datetime | None


class SystemStats:
    """Lightweight system statistics collector."""

    def __init__(self, log_file: str | None = None):
        """
        Initialize stats collector.

        Args:
            log_file: Path to log file (defaults to Config.LOG_FILE)
        """
        self.log_file = Path(log_file or Config.LOG_FILE or "signage.log")

    def get_stats(self) -> dict[str, Any]:
        """
        Collect all system statistics.

        Returns:
            Dictionary with system health metrics
        """
        stats = {
            "timestamp": Config.get_current_time(),
            "uptime": self._get_uptime(),
            "generators": self._get_generator_stats(),
            "recent_errors": self._get_recent_errors(),
            "disk_space": self._get_disk_space(),
            "images_generated": self._get_image_count(),
            "log_file_size": self._get_log_size(),
        }

        return stats

    def _get_uptime(self) -> dict[str, Any]:
        """Get system uptime from first log entry."""
        if not self.log_file.exists():
            return {"seconds": 0, "formatted": "Unknown"}

        try:
            with open(self.log_file) as f:
                first_line = f.readline()
                if match := re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", first_line):
                    first_time = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
                    uptime = datetime.now() - first_time
                    return {
                        "seconds": int(uptime.total_seconds()),
                        "formatted": self._format_duration(uptime.total_seconds()),
                    }
        except Exception as e:
            logger.debug(f"Could not determine uptime: {e}")

        return {"seconds": 0, "formatted": "Unknown"}

    def _get_generator_stats(self) -> dict[str, GeneratorStats]:
        """Get statistics for each generator (tesla, weather, etc)."""
        if not self.log_file.exists():
            return {}

        stats: dict[str, GeneratorStats] = defaultdict(
            lambda: GeneratorStats(success=0, failure=0, last_run=None)
        )
        cutoff_time = datetime.now() - timedelta(hours=24)

        try:
            with open(self.log_file) as f:
                for line in f:
                    # Parse timestamp
                    if not (match := re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line)):
                        continue

                    timestamp_str = match.group(1)
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                    # Only look at last 24 hours
                    if timestamp < cutoff_time:
                        continue

                    # Check for completion messages
                    if "✓" in line and "complete" in line.lower():
                        for source in [
                            "tesla",
                            "powerwall",
                            "weather",
                            "ferry",
                            "stock",
                            "speedtest",
                            "ambient",
                            "sensors",
                        ]:
                            if source.lower() in line.lower():
                                stats[source]["success"] += 1
                                last_run = stats[source]["last_run"]
                                if last_run is None or (
                                    isinstance(last_run, datetime) and timestamp > last_run
                                ):
                                    stats[source]["last_run"] = timestamp
                                break

                    # Check for failure messages
                    if "failed" in line.lower() or "error" in line.lower():
                        for source in [
                            "tesla",
                            "powerwall",
                            "weather",
                            "ferry",
                            "stock",
                            "speedtest",
                            "ambient",
                            "sensors",
                        ]:
                            if source.lower() in line.lower():
                                stats[source]["failure"] += 1
                                break

        except Exception as e:
            logger.error(f"Error parsing log file: {e}")

        # Convert defaultdict to regular dict
        return dict(stats)

    def _get_recent_errors(self, hours: int = 24, max_errors: int = 10) -> list[dict]:
        """Get recent errors from log file."""
        if not self.log_file.exists():
            return []

        errors = []
        cutoff_time = datetime.now() - timedelta(hours=hours)

        try:
            with open(self.log_file) as f:
                for line in f:
                    if "ERROR" not in line and "WARNING" not in line:
                        continue

                    # Parse timestamp
                    if match := re.match(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", line):
                        timestamp_str = match.group(1)
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")

                        if timestamp < cutoff_time:
                            continue

                        # Extract error message
                        level = "ERROR" if "ERROR" in line else "WARNING"
                        message = line.split(" - ", 1)[-1].strip() if " - " in line else line

                        errors.append(
                            {
                                "timestamp": timestamp,
                                "level": level,
                                "message": message[:200],  # Truncate long messages
                            }
                        )

        except Exception as e:
            logger.error(f"Error parsing errors: {e}")

        # Return most recent errors
        return sorted(errors, key=lambda x: x["timestamp"], reverse=True)[  # type: ignore[arg-type,return-value]  # Timestamp sorting
            :max_errors
        ]

    def _get_disk_space(self) -> dict[str, Any]:
        """Get disk space information."""
        try:
            usage = psutil.disk_usage(str(Config.OUTPUT_PATH))
            return {
                "total_gb": usage.total / (1024**3),
                "used_gb": usage.used / (1024**3),
                "free_gb": usage.free / (1024**3),
                "percent_used": usage.percent,
            }
        except Exception as e:
            logger.error(f"Error getting disk space: {e}")
            return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent_used": 0}

    def _get_image_count(self, days: int = 7) -> dict[str, int]:
        """Count images generated in the last N days."""
        counts: dict[str, int] = defaultdict(int)
        cutoff_time = datetime.now() - timedelta(days=days)

        try:
            for img_file in Config.OUTPUT_PATH.glob("*.png"):
                mtime = datetime.fromtimestamp(img_file.stat().st_mtime)
                if mtime >= cutoff_time:
                    # Extract source from filename
                    name = img_file.stem
                    source = name.split("_")[0] if "_" in name else name
                    counts[source] += 1
                    counts["total"] += 1

        except Exception as e:
            logger.error(f"Error counting images: {e}")

        return dict(counts)

    def _get_log_size(self) -> dict[str, Any]:
        """Get log file size."""
        if not self.log_file.exists():
            return {"size_mb": 0, "size_formatted": "0 B"}

        try:
            size_bytes = self.log_file.stat().st_size
            size_mb = size_bytes / (1024**2)

            if size_mb < 0.01:
                size_formatted = f"{size_bytes / 1024:.1f} KB"
            else:
                size_formatted = f"{size_mb:.1f} MB"

            return {"size_mb": size_mb, "size_formatted": size_formatted}
        except Exception as e:
            logger.error(f"Error getting log size: {e}")
            return {"size_mb": 0, "size_formatted": "0 B"}

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format seconds into human-readable duration."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"
        else:
            days = int(seconds / 86400)
            hours = int((seconds % 86400) / 3600)
            return f"{days}d {hours}h"
