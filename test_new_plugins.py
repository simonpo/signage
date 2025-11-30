#!/usr/bin/env python3
"""Test script for newly added plugins."""

import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables first, then import plugin modules
from dotenv import load_dotenv

load_dotenv()

# Import modules after dotenv is loaded
# Import sources to trigger registration
import src.plugins.sources  # noqa: E402, F401
from src.plugins.registry import SourceRegistry  # noqa: E402

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def test_plugin_registration():
    """Test that all new plugins are registered."""
    print("\n=== Testing Plugin Registration ===")

    registered_types = SourceRegistry.list_types()
    print(f"Registered plugin types: {registered_types}")

    new_plugins = ["speedtest", "stock", "system_health", "ferry_map"]

    for plugin_type in new_plugins:
        if plugin_type in registered_types:
            print(f"✓ {plugin_type} is registered")
        else:
            print(f"✗ {plugin_type} is NOT registered")
            return False

    return True


def test_plugin_creation():
    """Test that new plugins can be instantiated."""
    print("\n=== Testing Plugin Creation ===")

    test_configs = [
        {"id": "speedtest_test", "type": "speedtest", "config": {}},
        {"id": "stock_test", "type": "stock", "config": {}},
        {"id": "system_health_test", "type": "system_health", "config": {}},
        {"id": "ferry_map_test", "type": "ferry_map", "config": {}},
    ]

    for config in test_configs:
        try:
            plugin = SourceRegistry.create(
                source_type=config["type"], source_id=config["id"], config=config["config"]
            )
            print(f"✓ Created {config['type']} plugin: {plugin.__class__.__name__}")
        except Exception as e:
            print(f"✗ Failed to create {config['type']}: {e}")
            return False

    return True


def test_plugin_validation():
    """Test that new plugins pass validation."""
    print("\n=== Testing Plugin Validation ===")

    test_configs = [
        {"id": "speedtest_test", "type": "speedtest", "config": {}},
        {"id": "stock_test", "type": "stock", "config": {}},
        {"id": "system_health_test", "type": "system_health", "config": {}},
        {"id": "ferry_map_test", "type": "ferry_map", "config": {}},
    ]

    for config in test_configs:
        try:
            plugin = SourceRegistry.create(
                source_type=config["type"], source_id=config["id"], config=config["config"]
            )
            valid = plugin.validate_config()
            if valid:
                print(f"✓ {config['type']} validation passed")
            else:
                print(f"✗ {config['type']} validation failed")
                return False
        except Exception as e:
            print(f"✗ {config['type']} validation error: {e}")
            return False

    return True


def main():
    """Run all tests."""
    print("Testing newly added plugins...")

    tests = [
        ("Plugin Registration", test_plugin_registration),
        ("Plugin Creation", test_plugin_creation),
        ("Plugin Validation", test_plugin_validation),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            failed += 1

    print("\n=== Test Summary ===")
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")

    if failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
