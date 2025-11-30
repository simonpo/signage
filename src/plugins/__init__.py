"""Plugin system for signage data sources."""

from src.plugins.base_source import BaseSource, SourceMetrics
from src.plugins.executor import PluginExecutor
from src.plugins.registry import SourceRegistry

__all__ = ["BaseSource", "SourceMetrics", "SourceRegistry", "PluginExecutor"]
