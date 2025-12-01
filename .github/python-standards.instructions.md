---
description: 'Python code standards and engineering fundamentals for the signage project'
applyTo: '**/*.py'
---

# Python Engineering Standards - Signage Project

Engineering fundamentals standards based on Phase 1 completion. All Python code must comply with these requirements.

## Project Context

- **Project**: Samsung Frame TV Signage System
- **Python Version**: 3.9+ (specified in `.python-version`)
- **Code Formatter**: Black (line-length 100)
- **Linter**: Ruff + MyPy
- **CI/CD**: GitHub Actions (.github/workflows/ci.yml)
- **Dependency Management**: Exact version pinning in `requirements.txt` and `requirements-dev.txt`
- **Security**: Automated CVE scanning via `pip-audit` in CI
- **Phase**: Phase 1 Complete, Phase 2 (Testing) in progress

## Required Tools Configuration

All Python files must pass these checks before commit:

### 1. Black Formatting (P0 - Blocking)

```bash
black --check --diff .
```

**Configuration** (pyproject.toml):
- Line length: 100
- Target version: Python 3.9
- Format ALL files before committing

**Never commit code that fails `black --check`**

### 2. Ruff Linting (P0 - Blocking)

```bash
ruff check .
```

**Enabled Rules**:
- E/W: pycodestyle errors and warnings
- F: Pyflakes (unused imports, undefined names)
- I: isort (import sorting)
- N: pep8-naming
- UP: pyupgrade (modern Python syntax)
- B: flake8-bugbear (common bugs)
- C4: flake8-comprehensions
- SIM: flake8-simplify

**Common Issues to Avoid**:
- Unused imports (F401) - remove them
- Trailing whitespace (W291, W293) - clean it up
- Undefined names (F821) - fix references
- Unnecessary mode arguments like `open(file, "r")` - use `open(file)`

**Auto-fix many issues**: `ruff check --fix .`

### 3. Type Hints (P1 - Important)

```bash
mypy src/ --ignore-missing-imports
```

**Requirements**:
- Add type hints to all function signatures
- Use `Optional[Type]` for nullable values
- Use `list[str]`, `dict[str, Any]` (Python 3.9+ syntax)
- Import from `typing`: `Literal`, `Optional`, `Any`

**Example**:
```python
from typing import Optional

def get_vehicle_data(vehicle_id: str) -> Optional[dict]:
    """Fetch vehicle data from API."""
    ...
```

## Code Standards

### Import Organization

Order imports using isort (handled by ruff):

```python
# Standard library
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Third-party
import requests
from pydantic import BaseModel

# Local
from src.clients.base import APIClient
from src.config import Config
```

### Logging (P0 - Required)

All clients and modules must use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

# Use appropriate log levels
logger.debug("Detailed debugging info")
logger.info("Important events")
logger.warning("Warning conditions")
logger.error("Error conditions")

# Include context in error logs
logger.error(f"Failed to fetch data: {e}")
```

**Never use `print()` for production output** - use logging instead.

### Error Handling (P0 - Required)

All API clients inherit from `APIClient` base class which provides:

- **Retry logic** with exponential backoff
- **Circuit breaker** pattern for external services
- **Graceful degradation** (continue if one source fails)

**Pattern for new clients**:

```python
from src.clients.base import APIClient

class MyClient(APIClient):
    def __init__(self):
        super().__init__()

    def fetch_data(self) -> Optional[dict]:
        """Fetch data with automatic retries."""
        try:
            response = self._make_request(url, headers=headers)
            if response and response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed to fetch data: {e}")
            return None
```

### Configuration (P0 - Required)

All config uses Pydantic validation via `src/config.py`:

```python
from src.config import Config

# Access config values
api_key = Config.OPENWEATHER_API_KEY
region = Config.TESLA_REGION or "na"  # With default

# Never use os.getenv() directly - always use Config
```

**Benefits**:
- Fail-fast validation on startup
- Type safety
- Clear error messages for missing/invalid config

### Data Models

Use `@dataclass` for data structures:

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class VehicleData:
    """Tesla vehicle data from Fleet API."""

    battery_percent: float
    range_miles: float
    charging: bool
    climate_on: bool
    locked: bool
    odometer: float
    vehicle_name: Optional[str] = None
    alerts: list[str] = field(default_factory=list)
```

## File Organization

```
src/
  clients/        # API clients (inherit from APIClient)
  models/         # Data models (@dataclass, pydantic)
  renderers/      # HTML/PIL rendering engines
  backgrounds/    # Background image providers
  utils/          # Utilities (logging, caching, file management)
  config.py       # Pydantic config validation
```

### New Client Checklist

When adding a new data source client:

- [ ] Inherit from `APIClient` base class
- [ ] Add configuration to `src/config.py` with validation
- [ ] Document in `.env.example`
- [ ] Use structured logging (`logger.info`, `logger.error`)
- [ ] Return `Optional[Type]` for nullable results
- [ ] Create data model in `src/models/`
- [ ] Add type hints to all methods
- [ ] Run `black` and `ruff --fix` before committing
- [ ] Add to CI test suite (Phase 2)

## Security (P0 - Blocking)

**Never commit**:
- API keys, tokens, passwords
- `.env` files (gitignored)
- Private keys (`.pem`, `.key` files - gitignored)
- Token files (`.tesla_tokens.json` - gitignored)

**Always**:
- Use `Config` for secrets
- Add new secret files to `.gitignore`
- Store tokens in files outside git (like `.tesla_tokens.json`)
- Log token refresh events but never log token values

## CI/CD Requirements

All PRs must pass:

1. **Lint job**: `black --check`, `ruff check`, `mypy`
2. **Test job**: `pytest` with coverage
3. **Config validation**: Test .env schema

**CI failures are blocking** - fix before merge.

## Testing (Phase 2 - In Progress)

When Phase 2 is complete, all new code requires:

- Unit tests with 80%+ coverage
- Mocked API responses (use `responses` library)
- Type hints verified by mypy

## Common Patterns

### API Client Template

```python
"""
Client for [Service Name] API.
"""

import logging
from typing import Optional

from src.clients.base import APIClient
from src.config import Config

logger = logging.getLogger(__name__)


class ServiceClient(APIClient):
    """Client for [Service] API."""

    BASE_URL = "https://api.example.com"

    def __init__(self):
        """Initialize client."""
        super().__init__()

        if not Config.SERVICE_API_KEY:
            raise ValueError("SERVICE_API_KEY must be configured")

        self.api_key = Config.SERVICE_API_KEY

    def fetch_data(self) -> Optional[dict]:
        """Fetch data from service."""
        url = f"{self.BASE_URL}/endpoint"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        response = self._make_request(url, headers=headers)

        if response and response.status_code == 200:
            data = response.json()
            logger.info("Successfully fetched data")
            return data
        elif response:
            logger.error(f"API error {response.status_code}: {response.text}")

        return None
```

### Data Model → SignageContent

```python
from dataclasses import dataclass
from src.models.signage_data import SignageContent

@dataclass
class MyData:
    """Raw data from API."""

    value: float
    status: str

    def to_signage(self) -> SignageContent:
        """Convert to signage format for rendering."""
        return SignageContent(
            lines=[
                f"Status: {self.status}",
                f"Value: {self.value:.1f}",
            ],
            filename_prefix="mydata",
            layout_type="centered",
            background_mode="local",
            background_query="topic/subtype",
        )
```

## Validation Commands

Before every commit, run:

```bash
# Activate venv
source venv/bin/activate

# Format code
black .

# Fix auto-fixable issues
ruff check --fix .

# Check remaining issues
ruff check .

# Type checking
mypy src/ --ignore-missing-imports
```

Or use the CI locally:
```bash
# Run same checks as CI
black --check --diff .
ruff check .
mypy src/ --ignore-missing-imports
pytest tests/ -v
```

## Pre-commit Hooks

Pre-commit hooks are configured to run automatically before every commit:

```bash
# Install hooks (done once per clone)
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Skip hooks for urgent commits (use sparingly)
git commit --no-verify
```

**What runs before each commit:**
- Black formatting
- Ruff linting (with auto-fix)
- MyPy type checking
- Pytest test suite
- Trailing whitespace removal
- YAML validation
- Merge conflict detection

If any check fails, the commit is blocked. Fix the issues and commit again.

## Dependency Management

**Critical**: All dependencies MUST use exact version pinning.

### Requirements Files

- **requirements.txt**: Production dependencies only (exact versions with `==`)
- **requirements-dev.txt**: Development tools (extends requirements.txt with `-r requirements.txt`)

### Adding New Dependencies

```bash
# Activate venv
source venv/bin/activate

# Install new package
pip install package-name

# Get exact version
pip freeze | grep package-name

# Add to appropriate file with exact version
echo "package-name==X.Y.Z" >> requirements.txt
# OR for dev tools
echo "package-name==X.Y.Z" >> requirements-dev.txt
```

### Updating Dependencies

```bash
# Update specific package
pip install --upgrade package-name

# Capture new version
pip freeze | grep package-name

# Update in requirements file with new exact version
```

### Security Auditing

All dependencies are automatically scanned for CVEs via `pip-audit` in CI:

```bash
# Run locally
pip install pip-audit
pip-audit -r requirements.txt
pip-audit -r requirements-dev.txt
```

### Version Pinning Rules

- ✅ **Always**: `package==1.2.3` (exact version)
- ❌ **Never**: `package>=1.2.0` (minimum version)
- ❌ **Never**: `package` (unpinned)

**Exception**: Git dependencies like `samsungtvws` must specify exact commit hash.

### Why Exact Pins?

1. **Reproducible builds**: Same code = same dependencies = same behavior
2. **No surprises**: Updates are deliberate, not automatic
3. **CI/CD reliability**: Tests validate exact versions you deploy
4. **Security tracking**: Know exactly what you're running
5. **Rollback safety**: Can reproduce any previous state

## References

- **Action Plan**: `planning/action-plan.md` (local only, gitignored)
- **CI Config**: `.github/workflows/ci.yml`
- **Tool Config**: `pyproject.toml`
- **Base Client**: `src/clients/base.py`
- **Config Validation**: `src/config.py` (Pydantic-based)
- **Requirements**: `requirements.txt` (production), `requirements-dev.txt` (development)
- **Python Version**: `.python-version`

## Not Doing (Explicit Non-Goals)

- Dynamic typing (always use type hints)
- `print()` statements for logging
- Direct `os.getenv()` calls (use Config)
- Committing unformatted code
- Ignoring CI failures
- Unpinned or loosely-pinned dependencies (always exact versions)

---

**When in doubt**: Check existing clients like `src/clients/tesla_fleet.py` for patterns.
