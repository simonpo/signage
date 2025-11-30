"""Tests for plugin system."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from src.models.signage_data import SignageContent
from src.plugins.base_source import BaseSource, SourceMetrics
from src.plugins.config.loader import ConfigLoader
from src.plugins.config.schemas import SourceConfig, SourcesConfig
from src.plugins.executor import PluginExecutor
from src.plugins.registry import SourceRegistry


class TestSourceMetrics:
    """Test SourceMetrics dataclass."""

    def test_metrics_initialization(self):
        """Test creating metrics object."""
        now = datetime.now()
        metrics = SourceMetrics(
            source_id="test",
            source_type="test_type",
            started_at=now,
            completed_at=now,
            success=True,
            duration_seconds=1.5,
        )
        assert metrics.source_id == "test"
        assert metrics.source_type == "test_type"
        assert metrics.success is True
        assert metrics.duration_seconds == 1.5


class TestBaseSource:
    """Test BaseSource abstract class."""

    def test_base_source_cannot_be_instantiated(self):
        """Test that BaseSource is abstract."""
        with pytest.raises(TypeError):
            BaseSource("test_id", {})

    def test_concrete_source_implementation(self):
        """Test a concrete implementation of BaseSource."""

        class ConcreteSource(BaseSource):
            def fetch_data(self):
                return None

            def validate_config(self):
                return True

        source = ConcreteSource("test_source", {"key": "value"})
        assert source.source_id == "test_source"
        assert source.config == {"key": "value"}

    def test_validate_config_implementation(self):
        """Test validate_config in concrete class."""

        class ValidatedSource(BaseSource):
            def fetch_data(self):
                return None

            def validate_config(self):
                if "required_key" not in self.config:
                    raise ValueError("Missing required_key")
                return True

        source = ValidatedSource("test", {"required_key": "value"})
        assert source.validate_config() is True

    def test_should_render_default(self):
        """Test default _should_render behavior."""

        class SimpleSource(BaseSource):
            def fetch_data(self):
                return None

            def validate_config(self):
                return True

        source = SimpleSource("test", {})
        content = SignageContent(
            lines=["Test line 1", "Test line 2"], filename_prefix="test", layout_type="centered"
        )
        assert source._should_render(content) is True


class TestSourceRegistry:
    """Test SourceRegistry."""

    def test_registry_registration(self):
        """Test registering a source type."""

        @SourceRegistry.register("test_registry_type")
        class TestSource(BaseSource):
            def fetch_data(self):
                return None

            def validate_config(self):
                return True

        assert "test_registry_type" in SourceRegistry.list_types()

    def test_registry_create(self):
        """Test creating a source from registry."""

        @SourceRegistry.register("test_create_type")
        class TestSource(BaseSource):
            def fetch_data(self):
                return None

            def validate_config(self):
                return True

        source = SourceRegistry.create("test_create_type", "test_id", {})
        assert isinstance(source, TestSource)
        assert source.source_id == "test_id"

    def test_registry_create_unknown_type(self):
        """Test creating unknown source type raises error."""
        with pytest.raises(ValueError, match="Unknown source type"):
            SourceRegistry.create("nonexistent_type_xyz", "test_id", {})


class TestConfigLoader:
    """Test ConfigLoader."""

    def test_load_nonexistent_file(self):
        """Test loading nonexistent config file returns None."""
        config = ConfigLoader.load(Path("nonexistent_file_abc123.yaml"))
        assert config is None

    def test_load_valid_config(self):
        """Test loading a valid config file."""
        yaml_content = """
sources:
  - id: weather_test
    type: weather
    enabled: true
    schedule: "*/30 * * * *"
    config:
      mode: html
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            config_path = Path(f.name)

        try:
            config = ConfigLoader.load(config_path)
            assert config is not None
            assert len(config.sources) == 1
            assert config.sources[0].id == "weather_test"
            assert config.sources[0].type == "weather"
            assert config.sources[0].enabled is True
        finally:
            config_path.unlink()


class TestPluginExecutor:
    """Test PluginExecutor."""

    def test_executor_initialization(self):
        """Test creating executor with config."""
        config = SourcesConfig(sources=[])
        executor = PluginExecutor(config)
        assert executor.config == config

    @patch("src.plugins.executor.SourceRegistry.create")
    def test_executor_skip_disabled_source(self, mock_create):
        """Test that disabled sources are skipped."""
        config = SourcesConfig(
            sources=[
                SourceConfig(id="disabled_source", type="test", enabled=False, schedule="* * * * *")
            ]
        )

        executor = PluginExecutor(config)
        executor.run()

        # Source should not be created
        mock_create.assert_not_called()


class TestSourceConfig:
    """Test SourceConfig schema."""

    def test_source_config_creation(self):
        """Test creating a SourceConfig."""
        config = SourceConfig(
            id="weather_main",
            type="weather",
            enabled=True,
            schedule="*/30 * * * *",
            config={"mode": "html"},
        )
        assert config.id == "weather_main"
        assert config.type == "weather"
        assert config.enabled is True
        assert config.schedule == "*/30 * * * *"
        assert config.config["mode"] == "html"

    def test_source_config_defaults(self):
        """Test SourceConfig default values."""
        config = SourceConfig(id="test_source", type="test", schedule="* * * * *")
        assert config.enabled is True  # Default
        assert config.config == {}  # Default
        assert config.timeout == 30  # Default


class TestSourcesConfig:
    """Test SourcesConfig schema."""

    def test_sources_config_creation(self):
        """Test creating a SourcesConfig."""
        config = SourcesConfig(
            sources=[
                SourceConfig(id="weather", type="weather", enabled=True, schedule="*/30 * * * *")
            ]
        )
        assert len(config.sources) == 1
        assert config.sources[0].id == "weather"

    def test_sources_config_empty(self):
        """Test creating empty SourcesConfig."""
        config = SourcesConfig(sources=[])
        assert len(config.sources) == 0

    def test_sources_config_duplicate_ids(self):
        """Test that duplicate IDs are caught."""
        with pytest.raises(ValueError, match="Duplicate source IDs"):
            SourcesConfig(
                sources=[
                    SourceConfig(id="dup", type="test", schedule="* * * * *"),
                    SourceConfig(id="dup", type="test", schedule="* * * * *"),
                ]
            )
