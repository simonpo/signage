"""
Plugin registry for automatic source discovery.
Uses decorator pattern for clean registration.
"""

from typing import Any

from src.plugins.base_source import BaseSource


class SourceRegistry:
    """Registry for source plugins."""

    _sources: dict[str, type[BaseSource]] = {}

    @classmethod
    def register(cls, source_type: str):
        """
        Decorator to register a source plugin.

        Usage:
            @SourceRegistry.register('weather')
            class WeatherSource(BaseSource):
                ...
        """

        def decorator(source_class: type[BaseSource]):
            if source_type in cls._sources:
                raise ValueError(f"Source type '{source_type}' already registered")

            if not issubclass(source_class, BaseSource):
                raise TypeError(f"{source_class.__name__} must inherit from BaseSource")

            cls._sources[source_type] = source_class
            return source_class

        return decorator

    @classmethod
    def get(cls, source_type: str) -> type[BaseSource]:
        """Get source class by type."""
        if source_type not in cls._sources:
            raise ValueError(
                f"Unknown source type: {source_type}. " f"Available: {list(cls._sources.keys())}"
            )
        return cls._sources[source_type]

    @classmethod
    def list_types(cls) -> list[str]:
        """List all registered source types."""
        return list(cls._sources.keys())

    @classmethod
    def create(cls, source_type: str, source_id: str, config: dict[str, Any]) -> BaseSource:
        """
        Create a source instance.

        Args:
            source_type: Type of source (e.g., 'weather')
            source_id: Unique ID for this instance
            config: Plugin-specific configuration

        Returns:
            Initialized source instance
        """
        source_class = cls.get(source_type)
        return source_class(source_id=source_id, config=config)
