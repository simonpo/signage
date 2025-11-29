# Contributing to Signage

Thank you for your interest in contributing! This project welcomes contributions from the community.

## Getting Started

### Prerequisites

- Python 3.9 or higher
- Git
- A Samsung Frame TV (optional, for testing uploads)
- API keys for data sources you want to test

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/signage.git
   cd signage
   ```

2. **Run the setup script**
   ```bash
   ./scripts/setup.sh
   ```

3. **Configure your environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

4. **Activate the virtual environment**
   ```bash
   source venv/bin/activate
   ```

5. **Install development dependencies**
   ```bash
   pip install black ruff mypy pytest pytest-cov responses
   ```

6. **Verify your setup**
   ```bash
   pytest tests/
   ```

## Code Standards

This project follows strict code quality standards. All contributions must comply.

### Python Standards

Detailed standards are documented in `.github/python-standards.instructions.md`. Key requirements:

#### Formatting (P0 - Blocking)

**Black** - All code must be formatted with Black:
```bash
black .
```

Configuration in `pyproject.toml`:
- Line length: 100
- Target: Python 3.9

#### Linting (P0 - Blocking)

**Ruff** - All code must pass Ruff checks:
```bash
ruff check .
```

Auto-fix many issues:
```bash
ruff check --fix .
```

#### Type Hints (P1 - Important)

**MyPy** - Add type hints to all functions:
```bash
mypy src/ --ignore-missing-imports
```

Example:
```python
from typing import Optional

def fetch_data(api_key: str) -> Optional[dict]:
    """Fetch data from API."""
    ...
```

### Commit Messages

Follow **Conventional Commits** format:

```
<type>: <short description>

[optional body]
```

**Types:**
- `feat`: New feature or capability
- `fix`: Bug fix
- `test`: Adding or updating tests
- `refactor`: Code restructuring without behaviour change
- `docs`: Documentation changes
- `chore`: Maintenance tasks (dependencies, tooling)
- `perf`: Performance improvements
- `style`: Formatting changes

**Examples:**
```
feat: add rugby scores integration
test: add weather client with http mocking
fix: handle missing ferry departure data
docs: update readme with tesla setup
```

## Development Workflow

### Before Committing

Run all quality checks:

```bash
# Activate virtual environment
source venv/bin/activate

# Format code
black .

# Fix auto-fixable issues
ruff check --fix .

# Check remaining issues
ruff check .

# Type checking
mypy src/ --ignore-missing-imports

# Run tests
pytest tests/ -v

# Check coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Pre-commit Hooks (Optional)

Pre-commit hooks are not yet configured but planned. Until then, manually run formatters before committing.

### Testing Requirements

All new code should include tests:

- **Unit tests** with 80%+ coverage target
- **Mock external APIs** using `responses` library
- **Type hints** verified by mypy

Example test structure:
```python
import responses
from src.clients.my_client import MyClient

@responses.activate
def test_fetch_data():
    """Test data fetching with mocked API."""
    responses.add(
        responses.GET,
        "https://api.example.com/data",
        json={"status": "ok"},
        status=200
    )

    client = MyClient()
    result = client.fetch_data()

    assert result is not None
    assert result["status"] == "ok"
```

## Project Architecture

### Directory Structure

```
src/
  clients/        # API clients (inherit from APIClient)
  models/         # Data models (@dataclass, pydantic)
  renderers/      # HTML/PIL rendering engines
  backgrounds/    # Background image providers
  utils/          # Utilities (logging, caching, file management)
  config.py       # Pydantic config validation
```

### Adding a New Data Source

1. **Create API client** in `src/clients/`
   - Inherit from `APIClient` base class
   - Add configuration to `src/config.py`
   - Document in `.env.example`
   - Use structured logging

2. **Create data model** in `src/models/`
   - Use `@dataclass` for data structures
   - Implement `to_signage()` method

3. **Add tests** in `tests/`
   - Mock API responses
   - Test error handling
   - Verify data transformation

4. **Update documentation**
   - Add to README.md
   - Update ROADMAP.md if applicable

See existing clients like `src/clients/weather.py` for patterns.

## Pull Request Process

1. **Create a feature branch**
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes**
   - Follow code standards
   - Add tests
   - Update documentation

3. **Commit with conventional commits**
   ```bash
   git commit -m "feat: add new feature"
   ```

4. **Push to your fork**
   ```bash
   git push origin feat/your-feature-name
   ```

5. **Open a Pull Request**
   - Describe your changes
   - Link related issues
   - Ensure CI passes

### PR Checklist

- [ ] Code follows Black formatting
- [ ] Passes Ruff linting
- [ ] Type hints added (MyPy clean)
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Commit messages follow Conventional Commits
- [ ] CI/CD pipeline passes

## CI/CD Pipeline

All PRs must pass:

1. **Lint job**: `black --check`, `ruff check`, `mypy`
2. **Test job**: `pytest` with coverage
3. **Config validation**: Test .env schema

CI failures are blocking - fix before merge.

## Areas for Contribution

### High Priority

- Increase test coverage (currently 37%, target 80%+)
- Add pre-commit hooks
- Implement missing sports clients (rugby, cricket)
- Performance optimisations for HTML rendering

### Medium Priority

- Add more background providers
- Enhance layout templates
- Improve error messages
- Add health check endpoint for daemon mode

### Documentation

- API setup guides for each service
- Troubleshooting guide
- Architecture documentation
- Additional examples

See `ROADMAP.md` for planned features.

## Security

- Never commit `.env` files or API keys
- See `SECURITY.md` for security policy
- Report vulnerabilities privately via GitHub Security Advisories

## Code Review

All submissions require review before merging:

- Code quality and standards compliance
- Test coverage and quality
- Documentation completeness
- Security considerations
- Performance implications

## Questions?

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Open a GitHub Issue
- **Feature requests**: Open a GitHub Issue with `enhancement` label
- **Security**: See `SECURITY.md`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognised in release notes and the README.

Thank you for contributing! 🎉
