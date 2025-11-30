"""
Base source interface for plugin system.
All data source plugins inherit from BaseSource.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.models.signage_data import SignageContent


@dataclass
class SourceMetrics:
    """Execution metrics for a source."""

    source_id: str
    source_type: str
    started_at: datetime
    completed_at: datetime | None = None
    success: bool = False
    error: str | None = None
    duration_seconds: float | None = None
    data_points: int = 0


class BaseSource(ABC):
    """
    Abstract base class for all signage data sources.

    Plugins inherit from this class and implement:
    - fetch_data(): Retrieve and format data
    - validate_config(): Verify plugin-specific config
    """

    def __init__(self, source_id: str, config: dict[str, Any]):
        """
        Initialize source with ID and configuration.

        Args:
            source_id: Unique identifier for this source instance
            config: Plugin-specific configuration dict
        """
        self.source_id = source_id
        self.config = config

    @abstractmethod
    def fetch_data(self) -> SignageContent | None:
        """
        Fetch data and return SignageContent for rendering.

        Returns:
            SignageContent if successful, None on failure
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate plugin-specific configuration.

        Returns:
            True if config is valid

        Raises:
            ValueError: If config is invalid (with helpful message)
        """
        pass

    def _should_render(self, content: SignageContent) -> bool:
        """
        Optional hook for conditional rendering logic.

        Override in plugin to implement custom rules like:
        - Only render if value changed
        - Only render during specific hours
        - Only render if threshold exceeded

        Returns:
            True if content should be rendered (default)
        """
        return True

    def execute(self) -> tuple[SignageContent | None, SourceMetrics]:
        """
        Execute source fetch with metrics tracking.

        This is the main entry point called by the plugin system.
        Do NOT override this - implement fetch_data() instead.

        Returns:
            (SignageContent or None, SourceMetrics)
        """
        metrics = SourceMetrics(
            source_id=self.source_id,
            source_type=self.__class__.__name__,
            started_at=datetime.utcnow(),
        )

        try:
            # Validate config before execution
            self.validate_config()

            # Fetch data
            content = self.fetch_data()

            # Check if should render
            if content and not self._should_render(content):
                content = None

            # Record success
            metrics.success = content is not None
            metrics.data_points = len(content.lines) if content else 0

        except Exception as e:
            metrics.success = False
            metrics.error = str(e)
            content = None

        finally:
            metrics.completed_at = datetime.utcnow()
            metrics.duration_seconds = (metrics.completed_at - metrics.started_at).total_seconds()

        return content, metrics
