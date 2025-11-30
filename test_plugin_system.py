#!/usr/bin/env python3
"""Test the plugin system."""

import logging
from pathlib import Path

from dotenv import load_dotenv

# Import sources to register them
import src.plugins.sources  # noqa: F401

# Import plugin system
from src.plugins.config.loader import ConfigLoader
from src.plugins.executor import PluginExecutor

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    """Test plugin system."""
    print("=" * 60)
    print("Testing Plugin System")
    print("=" * 60)

    # Load config
    config_path = Path("sources.test.yaml")
    print(f"\n1. Loading config from {config_path}")
    config = ConfigLoader.load(config_path)

    if not config:
        print(f"ERROR: Could not load config from {config_path}")
        return

    print(f"   ✓ Loaded {len(config.sources)} source(s)")

    # Show registered sources
    from src.plugins.registry import SourceRegistry

    print(f"\n2. Registered source types: {SourceRegistry.list_types()}")

    # Create executor
    print("\n3. Creating executor")
    executor = PluginExecutor(config)
    print("   ✓ Executor created")

    # Run sources
    print("\n4. Executing sources")
    executor.run()

    print("\n" + "=" * 60)
    print("Plugin system test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
