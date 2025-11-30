# Plugin System Implementation Plan

**Created:** 2025-11-29
**Reference:** ADR-0001
**Status:** Ready to implement

## Overview

This document provides a detailed, step-by-step implementation plan for converting the existing CLI-based signage system to a YAML-based plugin architecture. Each phase includes specific files to create/modify, code patterns to follow, and testing strategies.

---

## Phase 1: MVP - Plugin Foundation (Weeks 1-2)

### Step 1.1: Directory Structure (Day 1)

**Create directories:**
```bash
mkdir -p src/plugins
mkdir -p src/plugins/sources
mkdir -p src/plugins/config
mkdir -p examples
```

**Files to create:**
- `src/plugins/__init__.py`
- `src/plugins/sources/__init__.py`
- `src/plugins/config/__init__.py`

### Step 1.2: Base Source Interface (Days 1-2)

**Create:** `src/plugins/base_source.py`

```python
"""
Base source interface for plugin system.
All data source plugins inherit from BaseSource.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from src.models.signage_data import SignageContent


@dataclass
class SourceMetrics:
    """Execution metrics for a source."""

    source_id: str
    source_type: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    success: bool = False
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
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
    def fetch_data(self) -> Optional[SignageContent]:
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

    def execute(self) -> tuple[Optional[SignageContent], SourceMetrics]:
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
            metrics.duration_seconds = (
                metrics.completed_at - metrics.started_at
            ).total_seconds()

        return content, metrics
```

**Tests to create:** `tests/test_base_source.py`
- Test abstract methods enforcement
- Test metrics tracking
- Test error handling
- Test conditional rendering hook

### Step 1.3: Plugin Registry (Day 2)

**Create:** `src/plugins/registry.py`

```python
"""
Plugin registry for automatic source discovery.
Uses decorator pattern for clean registration.
"""

from typing import Any, Type

from src.plugins.base_source import BaseSource


class SourceRegistry:
    """Registry for source plugins."""

    _sources: dict[str, Type[BaseSource]] = {}

    @classmethod
    def register(cls, source_type: str):
        """
        Decorator to register a source plugin.

        Usage:
            @SourceRegistry.register('weather')
            class WeatherSource(BaseSource):
                ...
        """

        def decorator(source_class: Type[BaseSource]):
            if source_type in cls._sources:
                raise ValueError(f"Source type '{source_type}' already registered")

            if not issubclass(source_class, BaseSource):
                raise TypeError(
                    f"{source_class.__name__} must inherit from BaseSource"
                )

            cls._sources[source_type] = source_class
            return source_class

        return decorator

    @classmethod
    def get(cls, source_type: str) -> Type[BaseSource]:
        """Get source class by type."""
        if source_type not in cls._sources:
            raise ValueError(
                f"Unknown source type: {source_type}. "
                f"Available: {list(cls._sources.keys())}"
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
```

**Tests to create:** `tests/test_registry.py`
- Test registration via decorator
- Test duplicate registration rejection
- Test get() with valid/invalid types
- Test create() instance creation
- Test list_types()

### Step 1.4: Configuration Schema (Days 3-4)

**Create:** `src/plugins/config/schemas.py`

```python
"""
Pydantic schemas for YAML configuration validation.
"""

import os
import re
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class RenderingConfig(BaseModel):
    """Rendering configuration for a source."""

    layout: str = "default"
    background: Literal["local", "unsplash", "pexels", "gradient"] = "local"
    background_query: Optional[str] = None


class RetryConfig(BaseModel):
    """Retry configuration."""

    enabled: bool = True
    max_attempts: int = Field(default=3, ge=1, le=10)
    backoff_seconds: list[int] = Field(default=[1, 2, 4])


class FallbackConfig(BaseModel):
    """Fallback configuration."""

    use_cached: bool = False
    max_age_hours: int = Field(default=24, ge=1, le=168)  # Max 1 week


class SourceConfig(BaseModel):
    """Configuration for a single source instance."""

    id: str = Field(..., description="Unique identifier")
    type: str = Field(..., description="Source type (e.g., 'weather')")
    enabled: bool = True
    schedule: str = Field(..., description="Cron expression")
    timeout: int = Field(default=30, ge=1, le=300)  # 1s to 5min
    config: dict[str, Any] = Field(default_factory=dict)
    rendering: RenderingConfig = Field(default_factory=RenderingConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    fallback: FallbackConfig = Field(default_factory=FallbackConfig)

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        """Validate ID format."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "ID must contain only letters, numbers, underscores, and hyphens"
            )
        return v

    @field_validator("schedule")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        """Basic cron expression validation."""
        parts = v.split()
        if len(parts) != 5:
            raise ValueError(
                f"Invalid cron expression: {v}. Must have 5 parts: min hour day month dow"
            )
        return v

    def expand_env_vars(self) -> "SourceConfig":
        """Expand ${VAR} references in config values."""
        expanded_config = {}
        for key, value in self.config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                expanded_value = os.getenv(env_var)
                if expanded_value is None:
                    raise ValueError(f"Environment variable {env_var} not set")
                expanded_config[key] = expanded_value
            else:
                expanded_config[key] = value

        self.config = expanded_config
        return self


class SourcesConfig(BaseModel):
    """Top-level configuration schema."""

    sources: list[SourceConfig]

    @field_validator("sources")
    @classmethod
    def validate_unique_ids(cls, v: list[SourceConfig]) -> list[SourceConfig]:
        """Ensure all source IDs are unique."""
        ids = [source.id for source in v]
        duplicates = [id for id in ids if ids.count(id) > 1]
        if duplicates:
            raise ValueError(f"Duplicate source IDs found: {set(duplicates)}")
        return v
```

**Create:** `src/plugins/config/loader.py`

```python
"""
Configuration loader for sources.yaml.
"""

import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from src.plugins.config.schemas import SourcesConfig

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and validate YAML configuration."""

    DEFAULT_PATH = Path("sources.yaml")

    @staticmethod
    def load(path: Optional[Path] = None) -> Optional[SourcesConfig]:
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
```

**Create example:** `examples/sources.yaml`

```yaml
# Example sources.yaml configuration
# See docs/PLUGIN_GUIDE.md for full documentation

sources:
  # Weather for home location
  - id: weather_home
    type: weather
    enabled: true
    schedule: "*/15 * * * *"  # Every 15 minutes
    timeout: 30
    config:
      city: Seattle
      api_key: ${OPENWEATHER_API_KEY}
    rendering:
      layout: modern_weather
      background: local
      background_query: weather/cloudy
    retry:
      enabled: true
      max_attempts: 3
      backoff_seconds: [1, 2, 4]
    fallback:
      use_cached: true
      max_age_hours: 24

  # Tesla vehicle
  - id: tesla_model_y
    type: tesla
    enabled: true
    schedule: "*/30 * * * *"  # Every 30 minutes
    timeout: 45
    config:
      vehicle_index: 0  # First vehicle
    rendering:
      layout: tesla_card
      background: local
      background_query: tesla/model_y

  # Ferry schedule
  - id: ferry_seattle_bainbridge
    type: ferry
    enabled: true
    schedule: "*/10 6-22 * * *"  # Every 10min, 6am-10pm
    timeout: 20
    config:
      route_id: 4
      terminal_id: 7
    rendering:
      layout: ferry_map
      background: local
      background_query: ferry/puget_sound
```

**Tests to create:** `tests/test_config_loader.py`
- Test valid YAML loading
- Test Pydantic validation errors
- Test unique ID enforcement
- Test cron validation
- Test environment variable expansion

### Step 1.5: Convert First Plugin - Weather (Days 4-5)

**Create:** `src/plugins/sources/weather_source.py`

```python
"""
Weather data source plugin.
Wraps WeatherClient from existing codebase.
"""

import logging
from typing import Optional

from src.clients.weather import WeatherClient
from src.plugins.base_source import BaseSource
from src.plugins.registry import SourceRegistry
from src.models.signage_data import SignageContent

logger = logging.getLogger(__name__)


@SourceRegistry.register("weather")
class WeatherSource(BaseSource):
    """Weather data source."""

    def validate_config(self) -> bool:
        """Validate weather config."""
        if "city" not in self.config:
            raise ValueError("Weather source requires 'city' in config")

        if "api_key" not in self.config:
            raise ValueError("Weather source requires 'api_key' in config")

        return True

    def fetch_data(self) -> Optional[SignageContent]:
        """Fetch weather data."""
        city = self.config["city"]
        api_key = self.config["api_key"]

        logger.info(f"Fetching weather for {city}")

        # Use existing client
        client = WeatherClient()
        weather_data = client.fetch_weather(city, api_key)

        if not weather_data:
            logger.warning(f"No weather data for {city}")
            return None

        # Convert to signage content
        return weather_data.to_signage()
```

**Update:** `src/plugins/sources/__init__.py`

```python
"""
Import all source plugins to register them.
"""

from src.plugins.sources.weather_source import WeatherSource

__all__ = ["WeatherSource"]
```

**Tests:** `tests/test_weather_source.py`
- Test config validation (missing city, missing api_key)
- Test fetch_data with mocked client
- Test execute() returns metrics
- Test integration with registry

### Step 1.6: Convert Second Plugin - Tesla (Day 5)

**Create:** `src/plugins/sources/tesla_source.py`

Similar pattern to weather source, wrapping `TeslaFleetClient`.

**Update:** `src/plugins/sources/__init__.py`

Add TeslaSource import.

### Step 1.7: Convert Third Plugin - Ferry (Day 6)

**Create:** `src/plugins/sources/ferry_source.py`

Similar pattern, wrapping `FerryClient`.

### Step 1.8: Backward Compatibility (Day 7)

**Update:** `generate_signage.py`

Add backward compatibility check at top of main():

```python
def main():
    """Main entry point."""
    # Check for plugin system config
    from src.plugins.config.loader import ConfigLoader

    config = ConfigLoader.load()

    if config:
        # Use plugin system
        from src.plugins.executor import PluginExecutor
        executor = PluginExecutor(config)
        executor.run()
        return

    # Otherwise use legacy CLI system
    logger.info("Using legacy CLI mode (sources.yaml not found)")
    # ... existing argparse code ...
```

### Step 1.9: Migration Tool (Days 8-9)

**Create:** `src/plugins/migrator.py`

```python
"""
Migration tool to generate sources.yaml from current .env configuration.
"""

import os
from pathlib import Path

import yaml


class ConfigMigrator:
    """Generate sources.yaml from environment variables."""

    def migrate(self) -> dict:
        """
        Analyze current .env and generate sources.yaml structure.

        Returns:
            Dict ready to write as YAML
        """
        sources = []

        # Detect weather config
        if os.getenv("OPENWEATHER_API_KEY"):
            sources.append(
                {
                    "id": "weather_default",
                    "type": "weather",
                    "enabled": True,
                    "schedule": "*/15 * * * *",
                    "config": {
                        "city": os.getenv("WEATHER_CITY", "Seattle"),
                        "api_key": "${OPENWEATHER_API_KEY}",
                    },
                }
            )

        # Detect Tesla config
        if os.getenv("TESLA_ACCESS_TOKEN"):
            sources.append(
                {
                    "id": "tesla_default",
                    "type": "tesla",
                    "enabled": True,
                    "schedule": "*/30 * * * *",
                    "config": {"vehicle_index": 0},
                }
            )

        # Detect Ferry config
        if os.getenv("FERRY_ROUTE_ID"):
            sources.append(
                {
                    "id": "ferry_default",
                    "type": "ferry",
                    "enabled": True,
                    "schedule": "*/10 * * * *",
                    "config": {
                        "route_id": int(os.getenv("FERRY_ROUTE_ID")),
                        "terminal_id": int(os.getenv("FERRY_TERMINAL_ID", 0)),
                    },
                }
            )

        return {"sources": sources}

    def write_config(self, output_path: Path = Path("sources.yaml")) -> None:
        """Write generated config to file."""
        config = self.migrate()

        with open(output_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)

        print(f"✓ Generated {output_path}")
        print(f"✓ Found {len(config['sources'])} source(s)")
        print("\nReview the generated file and adjust as needed.")
```

**Add CLI flag:**

```python
parser.add_argument(
    "--migrate",
    action="store_true",
    help="Generate sources.yaml from current .env configuration",
)
```

### Step 1.10: Documentation (Day 10)

**Create:** `docs/PLUGIN_GUIDE.md`

- Creating your first plugin
- Plugin lifecycle
- Configuration schema
- Testing plugins
- Best practices

**Update:** `README.md`

Add "Plugin System" section explaining:
- How to use sources.yaml
- How to migrate from CLI
- How to create custom plugins

### Step 1.11: Testing (Days 11-12)

**Integration tests:**
- Test full plugin execution flow
- Test backward compatibility paths
- Test migration tool output
- Test config validation edge cases

**Coverage target:** 80%+ for new plugin code

---

## Phase 2: Production Ready (Weeks 3-4)

### Step 2.1: Timeout Decorator (Day 13)

**Update:** `src/plugins/base_source.py`

Add timeout wrapper to `execute()` method:

```python
import signal
from contextlib import contextmanager

@contextmanager
def timeout(seconds: int):
    """Context manager for timeouts."""
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds}s")

    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

# In execute():
with timeout(self.config.get('timeout', 30)):
    content = self.fetch_data()
```

### Step 2.2: Circuit Breaker (Days 14-15)

**Create:** `src/plugins/circuit_breaker.py`

Implement circuit breaker with exponential backoff:
- Track failures per source
- Exponential backoff: 1min, 2min, 4min, 8min (max 30min)
- Auto-recovery on success

### Step 2.3: Retry Logic (Day 16)

**Update:** `src/plugins/base_source.py`

Add retry wrapper respecting `retry` config:

```python
for attempt in range(max_attempts):
    try:
        return self.fetch_data()
    except Exception as e:
        if attempt < max_attempts - 1:
            sleep(backoff_seconds[attempt])
        else:
            raise
```

### Step 2.4: Cached Fallback (Day 17)

**Create:** `src/plugins/cache.py`

- Store successful responses with timestamps
- Use cache if fresh fetch fails AND `use_cached: true`
- Respect `max_age_hours`

### Step 2.5: AsyncIO Conversion (Days 18-20)

**Major refactor:**
- Convert `BaseSource.fetch_data()` to async
- Update all source plugins to async
- Add asyncio executor
- Parallel execution with `asyncio.gather()`

This is the biggest change - allocate extra time for testing.

### Step 2.6: Metrics Persistence (Day 21)

**Create:** `src/plugins/metrics_store.py`

- Write metrics to JSON file after each execution
- Append-only log format
- Basic cleanup (keep last 7 days)

### Step 2.7: Enhanced Validation (Day 22)

**Update:** `src/plugins/config/schemas.py`

- Better cron validation (use `croniter` library)
- Validate source types exist in registry
- Cross-field validation

### Step 2.8: Integration Tests (Days 23-24)

- Test timeout enforcement
- Test circuit breaker state transitions
- Test retry with backoff
- Test cached fallback
- Test parallel execution
- Test metrics persistence

### Step 2.9: Docker Updates (Day 25)

**Update:** `Dockerfile`, `docker-compose.yml`

- Mount sources.yaml
- Add environment for config
- Update documentation

---

## Phase 3: Observability (Week 5)

### Step 3.1: OpenTelemetry Setup (Days 26-27)

**Add dependency:** `opentelemetry-api`, `opentelemetry-sdk`

**Create:** `src/plugins/tracing.py`

- Initialize tracer provider
- Configure exporters (console, Jaeger)
- Setup from config

### Step 3.2: Add Tracing Spans (Days 28-29)

**Update:**
- `BaseSource.execute()` - add span
- Client methods - add spans
- Renderer - add spans

**Span attributes:**
- source_id, source_type
- duration, success/failure
- error messages
- data point counts

### Step 3.3: Exporter Configuration (Day 30)

**Update:** `src/plugins/config/schemas.py`

Add tracing config:

```yaml
tracing:
  enabled: true
  exporter: console  # or jaeger, zipkin
  jaeger_endpoint: http://localhost:14268/api/traces
```

### Step 3.4: Documentation (Days 31-32)

**Create:** `docs/OBSERVABILITY.md`

- How to enable tracing
- How to use Jaeger UI
- Interpreting traces
- Performance debugging

### Step 3.5: Testing (Days 33-35)

- Test trace generation
- Test different exporters
- Test disabled tracing (no overhead)
- Performance benchmarks

---

## Conversion Checklist

### Existing Sources to Migrate

- [ ] Weather (`src/clients/weather.py`)
- [ ] Tesla (`src/clients/tesla_fleet.py`)
- [ ] Ferry (`src/clients/ferry.py`)
- [ ] Stock (`src/clients/stock.py`)
- [ ] Speedtest (`src/clients/speedtest.py`)
- [ ] System Health (`src/clients/system_health.py`)
- [ ] Ambient Weather (`src/clients/ambient_weather.py`)
- [ ] NFL (`src/clients/sports/nfl.py`)

### For Each Source Plugin

**Steps:**
1. Create `src/plugins/sources/{name}_source.py`
2. Inherit from `BaseSource`
3. Register with `@SourceRegistry.register('name')`
4. Implement `validate_config()`
5. Implement `fetch_data()` (wrap existing client)
6. Add to `src/plugins/sources/__init__.py`
7. Write tests in `tests/test_{name}_source.py`
8. Update examples/sources.yaml with example config
9. Document in PLUGIN_GUIDE.md

**Template:**

```python
import logging
from typing import Optional

from src.clients.{name} import {Name}Client
from src.plugins.base_source import BaseSource
from src.plugins.registry import SourceRegistry
from src.models.signage_data import SignageContent

logger = logging.getLogger(__name__)


@SourceRegistry.register("{name}")
class {Name}Source(BaseSource):
    """<Description> data source."""

    def validate_config(self) -> bool:
        """Validate config."""
        required = ["field1", "field2"]
        for field in required:
            if field not in self.config:
                raise ValueError(f"{self.__class__.__name__} requires '{field}' in config")
        return True

    def fetch_data(self) -> Optional[SignageContent]:
        """Fetch data."""
        logger.info(f"Fetching {self.source_id} data")

        # Extract config
        field1 = self.config["field1"]
        field2 = self.config["field2"]

        # Use existing client
        client = {Name}Client()
        data = client.fetch(field1, field2)

        if not data:
            logger.warning(f"No data from {self.source_id}")
            return None

        # Convert to signage
        return data.to_signage()
```

---

## Testing Strategy

### Unit Tests
- Each source plugin (config validation, fetch logic)
- Registry (registration, creation)
- Config loader (validation, env expansion)
- Circuit breaker (state transitions)
- Cache (storage, retrieval, expiry)

### Integration Tests
- Full execution flow (config → fetch → render)
- Backward compatibility (YAML vs CLI)
- Migration tool (generates valid config)
- Timeout enforcement
- Retry with backoff
- Parallel execution

### Performance Tests
- Benchmark parallel vs sequential
- Tracing overhead measurement
- Memory usage with many sources

### Acceptance Tests
- User can migrate existing setup
- User can create custom plugin
- User can configure multiple instances
- Errors have helpful messages

---

## Rollout Plan

### Week 1-2: Phase 1 MVP
- Feature branch: `feature/plugin-system-mvp`
- PR with detailed examples and docs
- Beta tag: `v0.10.0-beta.1`

### Week 3-4: Phase 2 Production
- Feature branch: `feature/plugin-reliability`
- PR with integration tests
- Beta tag: `v0.10.0-beta.2`

### Week 5: Phase 3 Observability
- Feature branch: `feature/plugin-observability`
- PR with observability docs
- Release: `v0.10.0` (stable)

### Post-Release
- Gather feedback
- Iterate on deferred features if requested
- Maintain backward compatibility for 2 releases

---

## Success Criteria

### Phase 1 Complete When:
- [ ] 3+ sources converted to plugins
- [ ] Backward compatibility working
- [ ] Migration tool generates valid config
- [ ] Documentation complete
- [ ] 80%+ test coverage

### Phase 2 Complete When:
- [ ] Timeouts enforced
- [ ] Circuit breaker prevents hammering
- [ ] Retry with backoff working
- [ ] Cached fallback functional
- [ ] Parallel execution faster than sequential
- [ ] All sources async

### Phase 3 Complete When:
- [ ] Traces generated correctly
- [ ] Multiple exporters working
- [ ] Documentation with examples
- [ ] Performance acceptable (<5% overhead)

### Overall Success:
- [ ] Existing users can migrate with `--migrate`
- [ ] New users can configure without code changes
- [ ] Contributors can add plugins easily
- [ ] System is more reliable than before
- [ ] Observability helps debug issues

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **Breaking existing setups** | Maintain CLI mode, provide migration tool, test thoroughly |
| **AsyncIO complexity** | Start simple, add async in Phase 2, extensive testing |
| **Config errors hard to debug** | Pydantic validation with clear messages, `--validate` command |
| **Performance regression** | Benchmark before/after, optimize parallel execution |
| **Plugin quality varies** | Provide clear examples, testing guidelines, code review |
| **Tracing overhead** | Make optional, benchmark, use sampling if needed |

---

## Open Questions

1. **Scheduler:** Should we implement a built-in scheduler or rely on external cron?
   - **Decision:** External cron for now (simpler). Built-in scheduler in Phase 4 if requested.

2. **Plugin distribution:** PyPI packages or git submodules?
   - **Decision:** Start with in-tree plugins. External distribution in Phase 4+.

3. **Config format:** YAML vs TOML vs JSON?
   - **Decision:** YAML (better for comments and multi-line strings).

4. **Metrics storage:** JSON files vs SQLite?
   - **Decision:** JSON (simpler, no DB dependency). SQLite in Phase 4+ if needed.

---

**Ready to begin Phase 1 implementation!**
