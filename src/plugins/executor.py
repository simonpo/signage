"""
Plugin executor - orchestrates source execution and rendering.
"""

import logging

from src.plugins.config.schemas import SourcesConfig
from src.plugins.registry import SourceRegistry
from src.renderers.image_renderer import SignageRenderer
from src.utils.file_manager import FileManager

logger = logging.getLogger(__name__)


class PluginExecutor:
    """Execute configured sources and render outputs."""

    def __init__(self, config: SourcesConfig):
        """
        Initialize executor with configuration.

        Args:
            config: Validated SourcesConfig
        """
        self.config = config
        self.file_mgr = FileManager()

    def run(self, source_filter: str | None = None) -> None:
        """
        Execute all enabled sources (or specific source if filter provided).

        Args:
            source_filter: Optional source ID to run (otherwise runs all enabled)
        """
        # Filter sources
        sources_to_run = [
            source
            for source in self.config.sources
            if source.enabled and (source_filter is None or source.id == source_filter)
        ]

        if not sources_to_run:
            if source_filter:
                logger.error(f"Source '{source_filter}' not found or disabled")
            else:
                logger.warning("No enabled sources to run")
            return

        logger.info(f"Running {len(sources_to_run)} source(s)")

        for source_config in sources_to_run:
            self._execute_source(source_config)

    def _execute_source(self, source_config) -> None:
        """Execute a single source and render output."""
        try:
            # Create source instance
            source = SourceRegistry.create(
                source_type=source_config.type,
                source_id=source_config.id,
                config=source_config.config,
            )

            logger.info(f"[{source_config.id}] Executing {source_config.type} source")

            # Execute source with metrics
            content, metrics = source.execute()

            # Log metrics
            if metrics.success:
                logger.info(
                    f"[{source_config.id}] Success - {metrics.data_points} data points "
                    f"in {metrics.duration_seconds:.2f}s"
                )
            else:
                logger.error(
                    f"[{source_config.id}] Failed - {metrics.error} "
                    f"(took {metrics.duration_seconds:.2f}s)"
                )
                return

            # Render if we have content
            if content:
                # Apply rendering config
                if source_config.rendering.background:
                    content.background_mode = source_config.rendering.background
                if source_config.rendering.background_query:
                    content.background_query = source_config.rendering.background_query
                if source_config.rendering.layout:
                    content.layout_type = source_config.rendering.layout

                # Generate filename from source ID
                filename = f"{source_config.id}.png"

                # Check if this needs special map rendering
                if content.metadata.get("use_map_renderer"):
                    # Use FerryMapRenderer for ferry map visualization
                    from pathlib import Path

                    from src.config import Config
                    from src.renderers.ferry_map_renderer import FerryMapRenderer

                    map_renderer = FerryMapRenderer()
                    vessels = content.metadata.get("vessels", [])
                    img = map_renderer.render_full_map(vessels)

                    # Save to art_folder
                    output_path = Path(Config.OUTPUT_DIR) / filename
                    img.save(output_path, "PNG", quality=95, optimize=True)
                    logger.info(f"[{source_config.id}] Rendered ferry map to {filename}")
                else:
                    # Standard rendering path
                    use_html = (
                        source_config.rendering.mode == "html"
                        if source_config.rendering.mode
                        else False
                    )
                    renderer = SignageRenderer(use_html=use_html)

                    # Render
                    from src.config import Config

                    timestamp = Config.get_current_time()
                    # Pass any metadata objects to renderer
                    renderer.render(
                        content, filename=filename, timestamp=timestamp, **content.metadata
                    )

                    logger.info(f"[{source_config.id}] Rendered to {filename}")

        except Exception as e:
            logger.error(f"[{source_config.id}] Exception during execution: {e}", exc_info=True)
