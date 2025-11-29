# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive test coverage for Stock client (9 tests, 100% coverage)
- Comprehensive test coverage for Speedtest client (12 tests, 100% coverage)
- Security scanning with pip-audit, bandit, and detect-secrets pre-commit hooks
- Type stubs for Pillow (types-Pillow)
- Build tools pinning (setuptools, wheel)
- CI workflow matrix testing for Python 3.11 and 3.12
- Playwright browser caching in CI for faster test runs
- Concurrency control in CI to cancel outdated workflow runs
- README badge maintenance documentation

### Changed
- Test coverage increased from 40.64% to 43.89%
- Total test count increased from 72 to 120 tests
- Updated pre-commit tool versions (ruff 0.14.6, mypy 1.18.2)
- Optimized pytest pre-commit hook to run only on changed files
- Consolidated CI lint and test jobs into single build job with matrix strategy
- Removed 31 unused dependencies (15 from production, 16 from dev)
- Fixed Python version to 3.11.11 throughout project

### Fixed
- MD5 usage security warning in cache_manager.py (added usedforsecurity=False)
- Dependency version mismatches between local and CI environments

### Removed
- Unused dependencies: selenium, beautifulsoup4, undetected-chromedriver, playwright-stealth, lxml, and 26 others

## [0.5.0] - 2025-11-28

### Added
- Tesla Fleet API integration with OAuth2 token management
- Powerwall energy monitoring support
- Enhanced weather display with 7 new OpenWeatherMap fields
- Ferry schedule and vessel tracking (WSDOT API)
- Sports scores (NFL, Football/Soccer, Cricket, Rugby)
- Stock market data display
- Ambient weather station integration
- Pydantic configuration validation
- Comprehensive CI/CD pipeline with GitHub Actions
- Pre-commit hooks (black, ruff, mypy, pytest)
- Branch protection with required status checks
- Test suite with 40%+ coverage (72 tests)
- CONTRIBUTING.md and SECURITY.md guides
- Structured logging with configurable levels
- Background image providers (Pexels, Unsplash, local, gradients)
- HTML rendering with Jinja2 templates
- PIL-based text rendering engine
- `--dry-run` flag for testing without TV upload

### Changed
- Migrated to modern Tesla Fleet API from legacy API
- Improved error handling with retry logic and circuit breaker
- Enhanced HTML templates with responsive design
- Refactored rendering pipeline for better modularity

### Fixed
- Black version pinning to ensure consistent formatting (24.10.0)
- Ruff linting errors across codebase
- Status check name confusion in branch protection
- Token refresh logic in Tesla client

### Security
- Secure credential handling (all secrets in .env)
- Private keys properly gitignored
- Token files excluded from version control

## [0.1.0] - 2024-11-XX

### Added
- Initial release with basic signage generation
- Samsung Frame TV integration
- Basic data sources (weather, home assistant)
- Simple text rendering

[Unreleased]: https://github.com/simonpo/signage/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/simonpo/signage/compare/v0.1.0...v0.5.0
[0.1.0]: https://github.com/simonpo/signage/releases/tag/v0.1.0
