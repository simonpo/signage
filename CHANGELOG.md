# CHANGELOG


## v0.8.0 (2025-11-29)

### Bug Fixes

- Pass Codecov token correctly to codecov-action v4
  ([#9](https://github.com/simonpo/signage/pull/9),
  [`058b86a`](https://github.com/simonpo/signage/commit/058b86a510ead9155938ab1704271a7465d827d4))

- Move token from 'env' to 'with.token' (required for v4) - Change 'file' to 'files' parameter (v4
  syntax) - Fixes 'Token required - not valid tokenless upload' error

- Restore simple semantic-release workflow ([#18](https://github.com/simonpo/signage/pull/18),
  [`016507e`](https://github.com/simonpo/signage/commit/016507ec184c4861365598eac56e37d68b2ee7b6))

- Remove complex PR-based release logic - Use simple version + publish approach - Works with
  enforce_admins: false branch protection

### Chores

- Add security scanning, type stubs, and pin build tools
  ([#15](https://github.com/simonpo/signage/pull/15),
  [`126cbdd`](https://github.com/simonpo/signage/commit/126cbdd0a24cf35425328f7f975f7e87b6fd8e6e))

- Add bandit==1.8.0 for Python security linting - Add types-Pillow==10.2.0.20240822 type stub - Pin
  setuptools==75.6.0 and wheel==0.45.1 in requirements-dev.txt - Add pip-audit pre-commit hook
  (scans requirements files) - Add bandit pre-commit hook (scans src/ with low severity) - Update
  mypy additional_dependencies to include types-Pillow - Fix MD5 usage in cache_manager.py with
  usedforsecurity=False

All security scans and tests pass (120 passed, 1 skipped).

- Add test and code style badges, update CHANGELOG ([#8](https://github.com/simonpo/signage/pull/8),
  [`2ad75b1`](https://github.com/simonpo/signage/commit/2ad75b14ce06e6014d90ca9c57ffd03a3a73bb6c))

- Add tests passing badge (93 passing) - Add black code style badge - Update CHANGELOG with PR #7
  test improvements - Stock client: 0% → 100% coverage (9 tests) - Speedtest client: 0% → 100%
  coverage (12 tests) - Overall: 40.64% → 43.89% coverage - Total tests: 72 → 93

- Optimize CI workflow and add semantic versioning
  ([#16](https://github.com/simonpo/signage/pull/16),
  [`e3a980d`](https://github.com/simonpo/signage/commit/e3a980d4add64512f75f10e09883316f350980d7))

* chore: optimize CI workflow with matrix testing and caching

- Add concurrency control to cancel outdated workflow runs - Consolidate lint and test into single
  build job - Add Python version matrix (3.11, 3.12) - Add Playwright browser caching for faster
  runs - Add job dependencies (config-validation and security need build) - Upload coverage only for
  Python 3.11 (avoid duplicates) - Use playwright install --with-deps for system dependencies

Benefits: - Faster CI runs with Playwright browser caching - Multi-version testing ensures
  compatibility - Reduced GitHub Actions minutes with concurrency control - Better job ordering with
  dependencies

Note: Test credentials in CI workflow are not real secrets

* docs: update changelog and test badge to 120 passing

- Update CHANGELOG.md with all changes from recent PRs - Update test count badge from 93 to 120 -
  Add README badge maintenance guide to copilot-instructions.md

* feat: add automated semantic versioning and releases

- Add python-semantic-release for automatic version management - Configure semantic-release in
  pyproject.toml - Add GitHub Actions workflow for manual release triggers - Update version from
  0.5.0 to 0.7.0 in pyproject.toml - Document release process in copilot-instructions.md

Features: - Analyzes conventional commits to determine version bumps - Auto-updates CHANGELOG.md
  from [Unreleased] section - Creates git tags and GitHub releases automatically - Manual workflow
  trigger with optional force flag

* chore: set version to 0.3.0

* chore: trigger CI re-run

- Optimize pytest and add secret scanning to pre-commit
  ([#14](https://github.com/simonpo/signage/pull/14),
  [`62a529b`](https://github.com/simonpo/signage/commit/62a529b0cfb10da4989defd5a7b93bc7fe92a71f))

- Optimize pytest hook to run on changed files only: - Changed pass_filenames: false -> true -
  Removed always_run: true - Added types: [python]

- Add detect-secrets hook for secret scanning - Prevents accidentally committing API keys, tokens,
  passwords - Uses Yelp/detect-secrets v1.5.0

This makes commits faster while adding security scanning.

- Remove unused dependencies and update tool versions
  ([#13](https://github.com/simonpo/signage/pull/13),
  [`3f35300`](https://github.com/simonpo/signage/commit/3f353001d7f250bb04e0ae93d1f2951fc55564da))

- Remove unused packages from requirements.txt: - selenium, undetected-chromedriver,
  playwright-stealth - beautifulsoup4, lxml, soupsieve - All selenium dependencies (trio, h11, etc.)
  - Total: 15 packages removed (~40% reduction)

- Remove transitive dependencies from requirements-dev.txt: - Pre-commit hook dependencies
  (auto-installed) - Tool dependencies (auto-installed by black/pytest/mypy) - Total: 16 packages
  removed (~50% reduction)

- Add pip-audit for security scanning - Add type stubs (types-requests, types-pytz)

- Update pre-commit tool versions to match requirements-dev.txt: - ruff: v0.7.4 → v0.14.6 - mypy:
  v1.13.0 → v1.18.2

- Update pyproject.toml mypy overrides (remove bs4, undetected_chromedriver)

Retained playwright (required for HTML→PNG rendering in src/utils/html_renderer.py)

All tests pass with Python 3.11.11 (120 passed, 1 skipped)

- Upgrade to Python 3.11.11 ([#11](https://github.com/simonpo/signage/pull/11),
  [`aed875e`](https://github.com/simonpo/signage/commit/aed875ef484e38305ad04116b2760ff56b861f16))

* chore: upgrade to Python 3.11.11

- Update .python-version from 3.9 to 3.11.11 - Update pyproject.toml tool configurations (black,
  ruff, mypy) - Update pre-commit config for Python 3.11 - All 93 tests passing with Python 3.11.11

* refactor: modernize type annotations to Python 3.10+ syntax

- Replace Optional[X] with X | None (161 fixes via ruff) - Replace typing.Callable with
  collections.abc.Callable - Leverages Python 3.11 native type union syntax - All 93 tests passing -
  Note: MyPy shows new warnings with stricter 3.11 checks (non-blocking)

* chore: require Python 3.11+ for X | None syntax

- Update pyproject.toml requires-python from >=3.9 to >=3.11 - Update CI workflow to use Python 3.11
  for all jobs - Required for modern type union syntax (PEP 604)

### Continuous Integration

- Disable automatic release trigger temporarily ([#19](https://github.com/simonpo/signage/pull/19),
  [`158cc08`](https://github.com/simonpo/signage/commit/158cc084082b4bb83a09cfd5ec67a646996c9659))

Remove push trigger to prevent failed releases on every commit. Will re-enable after verifying
  manual release works.

- Enable automatic releases on push to main ([#17](https://github.com/simonpo/signage/pull/17),
  [`7bcbce0`](https://github.com/simonpo/signage/commit/7bcbce093a2afc8cd5ca10d895936352859e0eb9))

* ci: enable automatic releases on push to main

- Add push trigger to release workflow - Releases now happen automatically after PR merges - Manual
  workflow_dispatch still available for force releases

* fix: semantic-release build_command must be string not boolean

### Features

- Implement professional dependency management ([#10](https://github.com/simonpo/signage/pull/10),
  [`18eefd9`](https://github.com/simonpo/signage/commit/18eefd9b87af9413ad92364e1e9ba2fa403a24b8))

- Split requirements.txt (prod) and requirements-dev.txt (dev) - Pin ALL dependencies to exact
  versions for reproducibility - Add .python-version file (3.9) for version managers - Add pip-audit
  security scanning to CI pipeline - Update README with requirements and dependency docs - Update
  setup.sh to prompt for dev vs prod install - Document dependency management in
  python-standards.instructions.md

### Testing

- Add comprehensive tests for Stock and Speedtest clients
  ([#7](https://github.com/simonpo/signage/pull/7),
  [`8e04c8d`](https://github.com/simonpo/signage/commit/8e04c8d63a2b1f4f2d3cb5735ae8babc81dd46a1))

- Add 9 tests for StockClient (Alpha Vantage API) - Success case with valid quote data - Empty
  response handling (rate limits/invalid symbol) - API error responses - HTTP 500 errors - Missing
  API key/symbol graceful handling - Malformed JSON handling - Missing fields with N/A defaults -
  Warning logs for missing config

- Add 12 tests for SpeedtestClient (Speedtest Tracker API) - Success case with full response - Error
  response handling (message != ok) - Missing required fields - HTTP 401 errors - Malformed JSON
  handling - Missing URL/token raises ValueError - URL trailing slash normalization - Various
  timestamp format handling - Missing/invalid timestamps default to Unknown - Optional URL field
  handling

Coverage improvements: - Stock client: 0% → 100% - Speedtest client: 0% → 100% - Overall coverage:
  40.64% → 43.89% (+3.25%) - Total tests: 72 → 93 (+21 tests)

All tests use responses library for HTTP mocking following established patterns from
  Tesla/Ferry/Weather tests.

- Improve test coverage (43.81% → 48.04%) ([#12](https://github.com/simonpo/signage/pull/12),
  [`30a36c8`](https://github.com/simonpo/signage/commit/30a36c887e59b668793ab5dfdd4f980fcffe2723))

* test: add comprehensive tests for config validation and file management

- Add 11 tests for SignageConfig validation (config_validator.py: 0% → 59.63%) - Add 16 tests for
  FileManager functionality (file_manager.py: 0% → 91.67%) - Add environment isolation fixture to
  prevent test interference - Update Python version badge from 3.9+ to 3.11+ in README - Fix mypy
  type hint error in Config.get_timezone() - Overall coverage improvement: 43.81% → 48.04%

* fix: use timezone-aware datetime in test_get_current_filename_without_date

Fixes CI failure due to timezone mismatch between local (US/Pacific) and CI (UTC). Use
  Config.get_current_time() instead of datetime.now() to match FileManager implementation.


## v0.5.0 (2025-11-28)

### Bug Fixes

- Correct status check names in branch protection docs
  ([#4](https://github.com/simonpo/signage/pull/4),
  [`6d6ad57`](https://github.com/simonpo/signage/commit/6d6ad577ba6bd1b5b9a7e2b0c0c7f390b3434e29))

The actual check names are 'Lint', 'Test', 'Config Validation' (not 'CI / Lint', etc). The 'CI /'
  prefix is just the display name shown in the GitHub UI.

Use 'gh api repos/.../commits/SHA/check-runs' to find actual names.

This was the root cause of repeated merge blocking issues.

### Chores

- Add CHANGELOG, version tagging prep, and --dry-run flag
  ([#6](https://github.com/simonpo/signage/pull/6),
  [`9c0b69f`](https://github.com/simonpo/signage/commit/9c0b69f87f4b9e0abf731f938d3a07e5583cac33))

* chore: add CHANGELOG, version tagging prep, and --dry-run flag

- Add CHANGELOG.md following Keep a Changelog format - Document v0.5.0 release with all major
  features - Add --dry-run flag to generate_signage.py for testing - Prepare for semantic versioning
  workflow

Addresses immediate feedback recommendations.

* docs: add status badges to README

Add badges for: - CI build status - Code coverage (Codecov) - MIT license - Python version
  requirement

Makes project health visible at a glance.

- Add pre-commit hooks for automated quality checks
  ([`c525af9`](https://github.com/simonpo/signage/commit/c525af991b4d0b38d69e95c6688c437a0d41ea4f))

### Documentation

- Add comprehensive CI/CD troubleshooting guide ([#3](https://github.com/simonpo/signage/pull/3),
  [`649901c`](https://github.com/simonpo/signage/commit/649901cc5390ad42a6ff3e8e24853e09de3768a5))

Add detailed troubleshooting section covering: - Black version mismatch diagnosis and resolution -
  Ruff linting error patterns - Pre-commit hook best practices - Branch protection status check
  configuration - Systematic debugging workflow - Version pinning importance

This documents lessons learned from PR #2 to prevent similar issues in future.

- Add CONTRIBUTING and SECURITY guides ([#5](https://github.com/simonpo/signage/pull/5),
  [`ef8aea6`](https://github.com/simonpo/signage/commit/ef8aea6f65ede9190cb59df2ea0725b96fdc763f))

Add comprehensive contribution guidelines covering: - Development setup and prerequisites - Code
  standards (black, ruff, mypy) - Testing requirements and patterns - PR process and review rubric -
  Adding new data sources tutorial

Add security policy covering: - Vulnerability reporting process - Supported versions - Security best
  practices

- Separate writing style to personal gitignored file
  ([#2](https://github.com/simonpo/signage/pull/2),
  [`88a50ca`](https://github.com/simonpo/signage/commit/88a50ca031f0c1b3e38b86ae88c9fe25021bcaaa))

* docs: separate writing style to personal gitignored file

* fix: pin black to 24.10.0 in CI to match pre-commit hooks

The CI was installing the latest black version which has different formatting rules than black
  24.10.0 used in pre-commit hooks. This caused lint failures even when code was formatted correctly
  locally.

Pinning to black==24.10.0 ensures consistent formatting between local development and CI
  environment.

* style: apply black 24.10.0 formatting

Reformatted all Python files to match black 24.10.0 style used in pre-commit hooks and CI. This
  resolves lint check failures caused by version differences between local black 25.11.0 and CI.

* chore: trigger CI re-run

* fix: use correct exception type in tesla test

Use requests.exceptions.HTTPError instead of generic exception types for test_complete_token_failure
  to match actual behavior.

- Test branch protection
  ([`6f2eda0`](https://github.com/simonpo/signage/commit/6f2eda036e77c0d931de52444ea7a866050662d2))

### Testing

- Add ferry client tests (84% coverage, +11 tests)
  ([`c2690c0`](https://github.com/simonpo/signage/commit/c2690c029ef36a690a9ad8bcc89f3d6f0eb82e9c))

- Add ferry client with wsdot api mocking (84% coverage, +10 tests)
  ([`89b4ef2`](https://github.com/simonpo/signage/commit/89b4ef2b7b05b0f87692920638ff0dee763a0718))

- Add football client tests (97% coverage, +7 tests)
  ([`ecfa140`](https://github.com/simonpo/signage/commit/ecfa14094827fc3bf4df50902bce711a6fbc9c9a))

- Add tesla client with oauth mocking (79% coverage, +8 tests)
  ([`8e9f901`](https://github.com/simonpo/signage/commit/8e9f9017fe59f0204f9f87fb30f5a7c75db37447))

- Add tesla fleet client tests (96% coverage, +18 tests)
  ([`d01b530`](https://github.com/simonpo/signage/commit/d01b53059ec9a11f74361d6c994b31c135d51a68))


## v0.7.0 (2025-11-25)

### Bug Fixes

- Restore missing Python scripts after history cleanup
  ([`99c4177`](https://github.com/simonpo/signage/commit/99c4177dd6aa0b2f1b3bce12e3d08da5b56b02fe))

### Chores

- Add art_folder/ placeholder with .gitkeep
  ([`14357ce`](https://github.com/simonpo/signage/commit/14357ce214bc138752593298a87546182b52bb5e))

- Block future art_folder/ image commits
  ([`3e7b614`](https://github.com/simonpo/signage/commit/3e7b6141187b2d0f393b90a700b4fcee203944e2))

- Untrack all images in art_folder/ (keep folder)
  ([`9fc4081`](https://github.com/simonpo/signage/commit/9fc4081b7d734a7911b092422e1066a07f92a475))

- Update .gitignore and untrack excluded files
  ([`cc0476e`](https://github.com/simonpo/signage/commit/cc0476eb8efaaf210fd539610873421a9b73b7ae))

- Update .gitignore for art_folder placeholder
  ([`061b8af`](https://github.com/simonpo/signage/commit/061b8aff33b377c5bc51607d5414f56cd7338d75))

### Documentation

- Add virtual environment setup to README
  ([`24e4920`](https://github.com/simonpo/signage/commit/24e49205a5196b8dbb4dcd7f0dfd02d819983478))

### Features

- Full .env secrets, secure config, locked deps, and a README
  ([`81d3d18`](https://github.com/simonpo/signage/commit/81d3d18ed8ad9d910206304a40487332c08f3055))
