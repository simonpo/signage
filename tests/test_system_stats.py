"""Tests for system stats collector."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.utils.system_stats import SystemStats


@pytest.fixture
def temp_log_file():
    """Create a temporary log file with test data."""
    # Use current date/time so logs are within 24-hour window
    now = datetime.now()
    base_time = now.strftime("%Y-%m-%d")

    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        # Write sample log entries (all within last hour to ensure they're captured)
        f.write(
            f"{base_time} {(now - timedelta(minutes=60)).strftime('%H:%M:%S')} [INFO] Logging to file: signage.log\n"
        )
        f.write(
            f"{base_time} {(now - timedelta(minutes=55)).strftime('%H:%M:%S')} [INFO] ✓ Weather signage complete - 42.08°F, Clear Sky\n"
        )
        f.write(
            f"{base_time} {(now - timedelta(minutes=50)).strftime('%H:%M:%S')} [INFO] ✓ Tesla signage complete - 80% battery, 237mi range\n"
        )
        f.write(
            f"{base_time} {(now - timedelta(minutes=45)).strftime('%H:%M:%S')} [ERROR] ✗ Ferry signage failed: Connection timeout\n"
        )
        f.write(
            f"{base_time} {(now - timedelta(minutes=40)).strftime('%H:%M:%S')} [INFO] ✓ Stock signage complete - MSFT $492.01\n"
        )
        f.write(
            f"{base_time} {(now - timedelta(minutes=35)).strftime('%H:%M:%S')} [INFO] ✓ Tesla signage complete - 79% battery, 235mi range\n"
        )
        f.write(
            f"{base_time} {(now - timedelta(minutes=30)).strftime('%H:%M:%S')} [ERROR] ✗ Tesla signage failed: 408 timeout\n"
        )

        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)


def test_system_stats_uptime(temp_log_file):
    """Test uptime calculation from log file."""
    stats = SystemStats(log_file=str(temp_log_file))
    result = stats.get_stats()

    assert "uptime" in result
    assert "seconds" in result["uptime"]
    assert "formatted" in result["uptime"]
    assert result["uptime"]["seconds"] >= 0


def test_system_stats_generator_stats(temp_log_file):
    """Test generator success/failure tracking."""
    stats = SystemStats(log_file=str(temp_log_file))
    result = stats.get_stats()

    assert "generators" in result
    generators = result["generators"]

    # Check weather (1 success, 0 failures)
    assert "weather" in generators
    assert generators["weather"]["success"] == 1
    assert generators["weather"]["failure"] == 0

    # Check tesla (2 success, 1 failure)
    assert "tesla" in generators
    assert generators["tesla"]["success"] == 2
    assert generators["tesla"]["failure"] == 1

    # Check ferry (0 success, 1 failure)
    assert "ferry" in generators
    assert generators["ferry"]["success"] == 0
    assert generators["ferry"]["failure"] == 1

    # Check stock (1 success, 0 failures)
    assert "stock" in generators
    assert generators["stock"]["success"] == 1
    assert generators["stock"]["failure"] == 0


def test_system_stats_recent_errors(temp_log_file):
    """Test recent error extraction."""
    stats = SystemStats(log_file=str(temp_log_file))
    result = stats.get_stats()

    assert "recent_errors" in result
    errors = result["recent_errors"]

    # Should have 2 error entries
    assert len(errors) == 2

    # Check error messages
    error_messages = [e["message"] for e in errors]
    assert any("Ferry" in msg for msg in error_messages)
    assert any("Tesla" in msg for msg in error_messages)


def test_system_stats_disk_space():
    """Test disk space monitoring."""
    stats = SystemStats()
    result = stats.get_stats()

    assert "disk_space" in result
    disk = result["disk_space"]

    assert "total_gb" in disk
    assert "used_gb" in disk
    assert "free_gb" in disk

    assert disk["total_gb"] > 0
    assert disk["free_gb"] >= 0
    assert disk["used_gb"] >= 0


def test_system_stats_timestamp():
    """Test that stats include current timestamp."""
    stats = SystemStats()
    result = stats.get_stats()

    assert "timestamp" in result
    assert isinstance(result["timestamp"], datetime)


def test_system_stats_nonexistent_log():
    """Test handling of missing log file."""
    stats = SystemStats(log_file="/nonexistent/path/to/log.log")
    result = stats.get_stats()

    # Should return default values without crashing
    assert "uptime" in result
    assert result["uptime"]["seconds"] == 0
    assert "generators" in result
    assert len(result["generators"]) == 0


def test_system_stats_empty_log():
    """Test handling of empty log file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False) as f:
        temp_path = Path(f.name)

    try:
        stats = SystemStats(log_file=str(temp_path))
        result = stats.get_stats()

        # Should handle empty log gracefully
        assert "generators" in result
        assert len(result["generators"]) == 0
    finally:
        temp_path.unlink(missing_ok=True)
