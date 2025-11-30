# Plugin System Guide

**Status:** Phase 1 MVP Complete
**Version:** 0.10.0-beta
**Last Updated:** 2025-11-29

## Overview

The signage project now includes a flexible plugin system that allows you to configure data sources via YAML instead of command-line arguments. This makes it easier to:

- Configure multiple instances of the same source type
- Set custom schedules per source
- Manage source-specific rendering options
- Enable/disable sources without code changes

## Quick Start

### 1. Migrate Existing Configuration

If you have an existing `.env` configuration, automatically generate `sources.yaml`:

```bash
python generate_signage.py --migrate
```

This will:
- Detect configured sources in your `.env`
- Generate a `sources.yaml` with sensible defaults
- Preserve your existing settings

### 2. Run the Plugin System

Once `sources.yaml` exists, the plugin system is used automatically:

```bash
python generate_signage.py
```

All enabled sources in `sources.yaml` will be executed.

### 3. Run a Specific Source

```bash
python generate_signage.py --source weather_home
```

## Configuration Format

### Basic Structure

```yaml
sources:
  - id: unique_source_id
    type: source_type
    enabled: true
    schedule: "*/15 * * * *"  # Cron expression
    timeout: 30
    config:
      # Source-specific configuration
    rendering:
      layout: layout_name
      background: local
      background_query: category/subcategory
    retry:
      enabled: true
      max_attempts: 3
      backoff_seconds: [1, 2, 4]
    fallback:
      use_cached: false
      max_age_hours: 24
```

### Configuration Fields

#### Required Fields

- **id**: Unique identifier for this source instance (alphanumeric, `_`, `-`)
- **type**: Source plugin type (e.g., `weather`, `tesla`, `ferry`)
- **schedule**: Cron expression for when to run (required but not yet enforced in Phase 1)

#### Optional Fields

- **enabled**: Whether source is active (default: `true`)
- **timeout**: Execution timeout in seconds (default: 30, max: 300)
- **config**: Source-specific configuration (see source documentation)
- **rendering**: Rendering configuration (layout, background)
- **retry**: Retry behavior configuration
- **fallback**: Fallback behavior when source fails

## Available Source Plugins

### Weather (`weather`)

Fetches weather data from OpenWeatherMap.

**Configuration:**

```yaml
- id: weather_home
  type: weather
  enabled: true
  schedule: "*/15 * * * *"
  timeout: 30
  config:
    city: Seattle
    api_key: ${WEATHER_API_KEY}
  rendering:
    layout: modern_weather
    background: local
    background_query: weather/cloudy
```

**Required config:**
- `city`: City name for weather lookup
- `api_key`: OpenWeatherMap API key (can use `${ENV_VAR}` syntax)

### Tesla (`tesla`)

Fetches Tesla vehicle data via Fleet API.

**Configuration:**

```yaml
- id: tesla_model_y
  type: tesla
  enabled: true
  schedule: "*/30 * * * *"
  timeout: 45
  config:
    vehicle_index: 0  # First vehicle (default: 0)
  rendering:
    layout: tesla_card
    background: local
    background_query: tesla/model_y
```

**Required config:**
- None (uses Tesla credentials from `.env`)

**Optional config:**
- `vehicle_index`: Which vehicle to use if you have multiple (default: 0)

### Ferry (`ferry`)

Fetches Washington State Ferries schedule and vessel locations.

**Configuration:**

```yaml
- id: ferry_schedule
  type: ferry
  enabled: true
  schedule: "*/10 6-22 * * *"  # Every 10min, 6am-10pm
  timeout: 20
  config: {}  # Uses FERRY_ROUTE and FERRY_HOME_TERMINAL from .env
  rendering:
    layout: ferry_map
    background: local
    background_query: ferry/puget_sound
```

**Required config:**
- None (currently uses `.env` configuration)
- Future: Will support `route_id` and `terminal_id` in config

### Ambient Weather (`ambient_weather`)

Fetches current weather from your personal Ambient Weather station.

**Configuration:**

```yaml
- id: ambient_weather_home
  type: ambient_weather
  enabled: true
  schedule: "*/15 * * * *"
  timeout: 30
  config: {}  # Uses AMBIENT_API_KEY and AMBIENT_APP_KEY from .env
  rendering:
    layout: default
    background: local
    background_query: weather/sunny
```

**Required config:**
- None (uses Ambient Weather API keys from `.env`)

### Ambient Sensors (`ambient_sensors`)

Displays all temperature and humidity sensors from your Ambient Weather station.

**Configuration:**

```yaml
- id: ambient_sensors_home
  type: ambient_sensors
  enabled: true
  schedule: "*/15 * * * *"
  timeout: 30
  config: {}  # Uses AMBIENT_API_KEY, AMBIENT_APP_KEY, and AMBIENT_SENSOR_NAMES from .env
  rendering:
    layout: default
    background: gradient
```

**Required config:**
- None (uses Ambient Weather API keys and sensor names from `.env`)
- Sensor names are configured in `.env` as JSON: `AMBIENT_SENSOR_NAMES={"1": "Chickens", "2": "Greenhouse"}`

### Speedtest (`speedtest`)

Fetches internet speed test results from Speedtest Tracker.

**Configuration:**

```yaml
- id: speedtest_home
  type: speedtest
  enabled: true
  schedule: "0 */4 * * *"  # Every 4 hours
  timeout: 60
  config: {}  # Uses SPEEDTEST_URL and SPEEDTEST_TOKEN from .env
  rendering:
    layout: default
    background: local
    background_query: speedtest/network
```

**Required config:**
- None (uses Speedtest Tracker URL and token from `.env`)

### Stock (`stock`)

Fetches stock quotes from Alpha Vantage API.

**Configuration:**

```yaml
- id: stock_portfolio
  type: stock
  enabled: true
  schedule: "0 9-16 * * 1-5"  # Every hour, 9am-4pm, weekdays only
  timeout: 30
  config: {}  # Uses STOCK_API_KEY and STOCK_SYMBOL from .env
  rendering:
    layout: default
    background: local
    background_query: stock/charts
```

**Required config:**
- None (uses Alpha Vantage API key and stock symbol from `.env`)

### System Health (`system_health`)

Monitors local system health including generator success rates, disk space, and errors.

**Configuration:**

```yaml
- id: system_health_local
  type: system_health
  enabled: true
  schedule: "*/5 * * * *"  # Every 5 minutes
  timeout: 20
  config: {}  # No config needed - monitors local system
  rendering:
    layout: default
    background: gradient
```

**Required config:**
- None (monitors local system automatically)

### Ferry Map (`ferry_map`)

Full-screen map showing all Washington State Ferry vessel positions in real-time.

**Configuration:**

```yaml
- id: ferry_map_puget_sound
  type: ferry_map
  enabled: false  # Disabled by default (alternative to ferry schedule)
  schedule: "*/10 6-22 * * *"  # Every 10min, 6am-10pm
  timeout: 20
  config: {}  # Uses Config for FERRY_ROUTE
  rendering:
    layout: full_map
    background: ferry_map
```

**Required config:**
- None (uses ferry route from `.env`)

**Notes:**
- Uses FerryMapRenderer for full-screen Pillow-based map rendering
- Alternative to the `ferry` source which shows schedule cards
- Typically disabled by default to avoid duplication

## Environment Variables

Use the `${VAR_NAME}` syntax to reference environment variables:

```yaml
config:
  api_key: ${WEATHER_API_KEY}
  secret: ${MY_SECRET}
```

Variables are expanded when the configuration is loaded. If a variable is not set, an error is raised.

## Rendering Configuration

Control how each source is rendered:

```yaml
rendering:
  layout: modern_weather        # Layout template name
  background: local              # Background provider: local, unsplash, pexels, gradient
  background_query: weather/rainy  # Query for background provider
```

**Background providers:**
- `local`: Use images from `backgrounds/` directory
- `unsplash`: Fetch from Unsplash API
- `pexels`: Fetch from Pexels API
- `gradient`: Generate gradient background

## Retry Configuration

Configure retry behavior for failed requests:

```yaml
retry:
  enabled: true
  max_attempts: 3
  backoff_seconds: [1, 2, 4]  # Exponential backoff
```

## Fallback Configuration

Use cached data when source fails:

```yaml
fallback:
  use_cached: true
  max_age_hours: 24  # Max age of cached data to use
```

## Schedule Expressions

Schedules use standard cron format:

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
* * * * *
```

**Examples:**

- `*/15 * * * *` - Every 15 minutes
- `0 */2 * * *` - Every 2 hours on the hour
- `0 9-17 * * 1-5` - Every hour from 9am-5pm, weekdays only
- `*/10 6-22 * * *` - Every 10 minutes, 6am-10pm

**Note:** In Phase 1, schedules are defined but not enforced. Use external cron or the `--daemon` mode for scheduling.

## Multiple Instances

You can configure multiple instances of the same source type:

```yaml
sources:
  - id: weather_seattle
    type: weather
    config:
      city: Seattle
      api_key: ${WEATHER_API_KEY}

  - id: weather_portland
    type: weather
    config:
      city: Portland
      api_key: ${WEATHER_API_KEY}
```

## Validation

The configuration is validated when loaded:

- IDs must be unique
- Cron expressions must be valid
- Required config fields must be present
- Enum values (background types) must be valid

Invalid configurations will fail with helpful error messages.

## Backward Compatibility

The plugin system is fully backward compatible:

- If `sources.yaml` doesn't exist, the CLI mode is used
- Old command-line arguments (`--source weather`) still work
- Existing `.env` configuration is preserved

## Creating Custom Plugins

### Plugin Template

```python
"""
My custom data source plugin.
"""

import logging
from typing import Optional

from src.models.signage_data import SignageContent
from src.plugins.base_source import BaseSource
from src.plugins.registry import SourceRegistry

logger = logging.getLogger(__name__)


@SourceRegistry.register("mytype")
class MySource(BaseSource):
    """My custom data source."""

    def validate_config(self) -> bool:
        """Validate plugin-specific configuration."""
        if "required_field" not in self.config:
            raise ValueError("MySource requires 'required_field' in config")
        return True

    def fetch_data(self) -> Optional[SignageContent]:
        """Fetch data and return SignageContent for rendering."""
        logger.info(f"[{self.source_id}] Fetching data...")

        # Fetch your data here
        data = self._fetch_from_somewhere()

        if not data:
            logger.warning(f"[{self.source_id}] No data available")
            return None

        # Convert to SignageContent
        return SignageContent(
            lines=["Line 1", "Line 2"],
            filename_prefix="mydata",
            layout_type="centered",
            background_mode="local",
            background_query="category/subtype",
        )
```

### Registration

Add your plugin to `src/plugins/sources/__init__.py`:

```python
from src.plugins.sources.my_source import MySource

__all__ = [..., "MySource"]
```

### Configuration

Use your plugin in `sources.yaml`:

```yaml
- id: my_custom_source
  type: mytype
  schedule: "*/5 * * * *"
  config:
    required_field: value
```

## Troubleshooting

### Configuration Validation Errors

**Error:** `ValueError: Environment variable X not set`
- **Solution:** Ensure variable is defined in `.env` and you've run `source .env` or use `python-dotenv`

**Error:** `Invalid cron expression`
- **Solution:** Verify cron format at [crontab.guru](https://crontab.guru)

**Error:** `Duplicate source IDs found`
- **Solution:** Each source must have a unique `id`

### Source Execution Errors

**Error:** `Unknown source type: xyz`
- **Solution:** Check that the plugin is imported in `src/plugins/sources/__init__.py`

**Error:** `Source requires 'field' in config`
- **Solution:** Add the required configuration field to your source

## Future Enhancements (Phase 2+)

The following features are planned for future phases:

- **Phase 2:** Timeout enforcement, circuit breakers, async execution
- **Phase 3:** OpenTelemetry tracing and observability
- **Phase 4:** Built-in scheduler (no external cron needed)
- **Phase 5:** Plugin distribution via PyPI

## Examples

See `examples/sources.yaml` for a complete working example with all three source types.

---

**Need help?** Check the implementation plan at `docs/PLUGIN_IMPLEMENTATION_PLAN.md` or the ADR at `docs/adr/001-plugin-system-architecture.md`.
