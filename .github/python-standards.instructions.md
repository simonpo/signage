---
description: 'Python code standards and engineering fundamentals for the signage project'
applyTo: '**/*.py'
---

# Python Engineering Standards

All Python code must comply with these requirements.

## Core Tools (All P0 - Blocking)

### Black Formatting
```bash
black .  # Format all files before committing
```
Line length: 100, Target: Python 3.9+

### Ruff Linting
```bash
ruff check --fix .  # Auto-fix issues
ruff check .        # Check remaining
```
Covers: pycodestyle, pyflakes, isort, pep8-naming, bugbear, comprehensions

### MyPy Type Checking
```bash
mypy src/ --ignore-missing-imports
```

**All function signatures require type hints:**
```python
from typing import Any

# ✅ Good
def get_data(vehicle_id: str) -> dict[str, Any] | None:
    items: list[str] = []  # Annotate when mypy can't infer
    return {"id": vehicle_id}

# ❌ Bad - missing types
def get_data(vehicle_id):
    return {"id": vehicle_id}
```

**Use Python 3.9+ syntax:**
- `str | None` not `Optional[str]`
- `list[str]` not `List[str]`
- Import from typing: `Any`, `Literal`, `TypedDict`

**Handle None properly:**
```python
def calc(timestamp: datetime | None) -> float:
    if timestamp is None:
        return 0.0
    return (datetime.now() - timestamp).total_seconds()
```

**PIL/Pillow uses tuples, not lists:**
```python
draw.rectangle((x, y, x + w, y + h), fill=color)  # ✅
draw.rectangle([x, y, x + w, y + h], fill=color)  # ❌
```

**type: ignore only with explanation:**
```python
return response.json()  # type: ignore[no-any-return]  # JSON from API
```

Module overrides in `pyproject.toml`: `src.config`, `src.utils.template_renderer`

## Code Standards

### Logging
```python
import logging
logger = logging.getLogger(__name__)

logger.info("Event")
logger.error(f"Failed: {e}")
```
Never use `print()` in production code.

### Configuration
```python
from src.config import Config

api_key = Config.SERVICE_API_KEY
region = Config.REGION or "default"
```
Never use `os.getenv()` directly. Pydantic validates on startup.

### Data Models
```python
from dataclasses import dataclass, field

@dataclass
class VehicleData:
    battery: float
    range: float
    alerts: list[str] = field(default_factory=list)
```

### API Clients
Inherit from `APIClient` for retry logic, circuit breaker, graceful degradation:

```python
from src.clients.base import APIClient

class MyClient(APIClient):
    def fetch_data(self) -> dict[str, Any] | None:
        try:
            response = self._make_request(url, headers=headers)
            if response and response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            logger.error(f"Failed: {e}")
            return None
```

## File Organization
```
src/
  clients/      # API clients (inherit APIClient)
  models/       # Data models (dataclass, pydantic)
  renderers/    # HTML/PIL rendering
  backgrounds/  # Background providers
  utils/        # Utilities
  config.py     # Pydantic validation
```

## Security (P0)

Never commit:
- API keys, tokens, passwords
- `.env` files
- Private keys (`.pem`, `.key`)
- Token files (`.tesla_tokens.json`)

Always:
- Use `Config` for secrets
- Add secrets to `.gitignore`
- Never log token values

## Dependency Management

**Exact version pinning required:**
```bash
pip install package-name
pip freeze | grep package-name
echo "package-name==X.Y.Z" >> requirements.txt
```

- ✅ `package==1.2.3`
- ❌ `package>=1.2.0`
- ❌ `package`

Why: Reproducible builds, no surprises, CI reliability, security tracking.

Files:
- `requirements.txt` - Production (exact versions `==`)
- `requirements-dev.txt` - Dev tools (extends requirements.txt)

Security: `pip-audit` runs in CI on all PRs.

## CI/CD

All PRs must pass:
1. Black, Ruff, MyPy
2. Pytest with coverage
3. Config validation

CI failures block merges.

## Pre-commit Hooks

```bash
pre-commit install              # Once per clone
pre-commit run --all-files      # Manual run
git commit --no-verify          # Skip (use sparingly)
```

Runs: Black, Ruff, MyPy, Pytest, whitespace cleanup, YAML validation.

## Quick Reference

**Before commit:**
```bash
source venv/bin/activate
black .
ruff check --fix .
mypy src/ --ignore-missing-imports
```

**New client checklist:**
- [ ] Inherit from `APIClient`
- [ ] Add config to `src/config.py`
- [ ] Use structured logging
- [ ] Return `Type | None` for nullable
- [ ] Create data model in `src/models/`
- [ ] Full type hints
- [ ] Run black, ruff, mypy

**Not allowed:**
- Dynamic typing (always type hints)
- `print()` for logging
- Direct `os.getenv()`
- Unformatted code
- Unpinned dependencies

---

Check existing clients like `src/clients/tesla_fleet.py` for patterns.
