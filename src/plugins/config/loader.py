"""
Configuration loader for sources.yaml.
"""

import logging
from pathlib import Path

import yaml
from pydantic import ValidationError

from src.plugins.config.schemas import SourcesConfig

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and validate YAML configuration."""

    DEFAULT_PATH = Path("sources.yaml")

    @staticmethod
    def load(path: Path | None = None) -> SourcesConfig | None:
        """
        Load and validate sources.yaml.

        Args:
            path: Path to config file (default: sources.yaml)

        Returns:
            Validated SourcesConfig or None if file doesn't exist

        Raises:
            ValidationError: If config is invalid
            yaml.YAMLError: If YAML is malformed
        """
        config_path = path or ConfigLoader.DEFAULT_PATH

        if not config_path.exists():
            logger.info(f"Config file {config_path} not found")
            return None

        logger.info(f"Loading configuration from {config_path}")

        with open(config_path) as f:
            raw_config = yaml.safe_load(f)

        try:
            config = SourcesConfig(**raw_config)

            # Expand environment variables
            for source in config.sources:
                source.expand_env_vars()

            logger.info(f"Loaded {len(config.sources)} source(s)")
            return config

        except ValidationError as e:
            logger.error(f"Configuration validation failed:\n{e}")
            raise
