## Commit Message Standards

Follow **Conventional Commits** format for all commits:

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
- `style`: Formatting changes (white-space, etc.)

**Guidelines:**
- Keep the first line under 72 characters
- Use imperative mood ("add feature" not "added feature")
- No full stop at the end of the subject line
- Separate subject from body with a blank line
- Body is optional but useful for explaining *why*

**Examples:**
```
feat: add tesla fleet api integration
test: add weather client with http mocking
fix: handle missing ferry departure data
docs: update readme with tesla setup
refactor: extract template rendering logic
```

## Code Standards

For Python code standards (formatting, linting, testing), see [python-standards.instructions.md](python-standards.instructions.md).

## README Badge Maintenance

**Test Count Badge** (line 4 of README.md):
- Manually update when test count changes significantly
- Current format: `[![Tests](https://img.shields.io/badge/tests-XXX%20passing-success)]`
- Update the `XXX` number after running `pytest tests/ -v`
- This is a static shields.io badge, not dynamic from CI
- Check count with: `pytest tests/ -v | grep "passed"`

**Other badges are dynamic and don't need updates:**
- CI status badge (auto-updates from GitHub Actions)
- codecov badge (auto-updates from codecov.io uploads)
- Code style, License, Python version (static metadata)

## Branch Protection Workflow

This repository uses branch protection on `main`. Before implementing code changes, **always check the current branch**.

**Rules:**
- ✅ Feature work: Must be on a feature branch (`feature/*`, `fix/*`, `test/*`, etc.)
- ✅ Documentation: Can be on `main` (*.md files, docs/)
- ❌ Code changes: Never commit directly to `main`

**Before creating new code, check the branch:**

```bash
git branch --show-current
```

**If on `main` and implementing code changes:**
1. Stop and inform the user
2. Suggest they create a feature branch:
   ```bash
   git checkout -b feature/descriptive-name
   ```
3. Wait for confirmation before proceeding

**Acceptable branch patterns:**
- `feature/*` - New features
- `fix/*` - Bug fixes
- `test/*` - Test improvements
- `refactor/*` - Code refactoring
- `docs/*` - Documentation only
- `chore/*` - Maintenance tasks

**If user is on `main` and requests code changes, respond:**

"You're currently on the `main` branch, which is protected. Please create a feature branch first:

\`\`\`bash
git checkout -b feature/your-feature-name
\`\`\`

Once you've switched branches, I'll proceed with the implementation."

**Exception:** Doc-only changes (README.md, *.md in root) can proceed on `main`.

## CI/CD and Testing Guidelines

### Critical: Understanding CI Failures

When CI fails, **diagnose methodically**:

1. **Identify which job failed**: lint, test, or config-validation
2. **Read the actual error output** - don't assume what's wrong
3. **CI runs ALL checks, not just PR diff** - formatting issues anywhere in the repo will fail CI

### Common CI Failure Patterns

**Black formatting failures:**
- **Symptom**: `would reformat X files` in CI but local `black --check .` passes
- **Root Cause**: Version mismatch between local and CI
- **Solution**:
  - Check `.pre-commit-config.yaml` for black version (currently 24.10.0)
  - Ensure `.github/workflows/ci.yml` pins same version: `pip install black==24.10.0`
  - Reinstall locally: `pip install black==24.10.0 --force-reinstall`
  - Run `black .` to reformat with correct version
  - **Never assume local black is correct** - CI version is authoritative

**Ruff linting failures:**
- **Symptom**: CI shows `Found X errors` but wasn't obvious from black output
- **Root Cause**: Lint job runs BOTH black AND ruff sequentially
- **Solution**:
  - Read entire CI log, don't stop at first error
  - Run `ruff check .` locally to see all issues
  - Use `ruff check --fix .` for auto-fixable issues
  - Common issues: unused variables (F841), bare Exception (B017)

**Test failures after "safe" changes:**
- **Symptom**: Changed exception type to fix ruff, now test fails
- **Root Cause**: Test expects specific exception type
- **Solution**:
  - Run the specific test locally: `pytest path/to/test.py::TestClass::test_name -v`
  - Match exception type to what's actually raised (check imports!)
  - For requests errors: use `requests.exceptions.HTTPError`, not generic `Exception`

### Pre-commit Hook Best Practices

**Before committing:**
1. Pre-commit hooks will auto-fix many issues (trailing whitespace, etc.)
2. If hooks fail, **read the output** - files may have been modified
3. Re-stage modified files: `git add <file>`
4. Commit again - hooks run again on new staged content
5. **Use `--no-verify` sparingly** - it defeats the purpose of hooks

**Bypassing hooks:**
- Only use `git commit --no-verify` when hooks are broken or during emergencies
- Document WHY you bypassed in commit message
- Fix the underlying issue ASAP

### Branch Protection and Status Checks

**Current Configuration:**
- Required status checks: `Lint`, `Test`, `Config Validation`
- Strict mode: `false` (checks don't need to re-run on merge commit)
- Required approving reviews: 0 (admin can merge without approval)

**CRITICAL: Status check names vs display names:**
- GitHub UI shows: `CI / Lint (pull_request)` ← This is the DISPLAY NAME
- Actual check name: `Lint` ← This is what goes in branch protection
- **Always use the actual check name, not the display name**

**How to find the correct check names:**
```bash
# Get check names from a recent commit
gh api repos/OWNER/REPO/commits/SHA/check-runs --jq '.check_runs[] | .name'

# Example output:
# Lint
# Test
# Config Validation
```

**Common mistakes:**
- ❌ Using `"CI / Lint"` (display name from GitHub UI)
- ❌ Using `"lint"` (lowercase job name)
- ✅ Using `"Lint"` (actual check run name)

**If unable to merge PR:**
1. Check status check names match exactly (see above)
2. Ensure `strict: false` in branch protection
3. Verify checks actually passed (not just pending)
4. Last resort: temporarily disable status checks, merge, re-enable

**Updating branch protection:**
```bash
gh api repos/simonpo/signage/branches/main/protection \
  --method PUT --input - <<'EOF'
{
  "required_status_checks": {
    "strict": false,
    "checks": [
      {"context": "Lint"},
      {"context": "Test"},
      {"context": "Config Validation"}
    ]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {"required_approving_review_count": 0},
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "restrictions": null
}
EOF
```

### Debugging Workflow

**When CI fails repeatedly:**

1. **Stop and analyze** - don't keep pushing hoping it fixes itself
2. **Run CI commands locally** in exact order:
   ```bash
   black --check --diff .
   ruff check .
   mypy src/ --ignore-missing-imports
   pytest tests/ -v
   ```
3. **Check versions match CI**:
   - Python version (CI uses 3.9)
   - Black version (currently 24.10.0)
   - Tool versions in requirements.txt
4. **Read ENTIRE error output** - later errors often more relevant than first
5. **Fix root cause, not symptoms** - version mismatches, not individual files

**Red flags:**
- ⚠️ "It works locally but fails in CI" → version mismatch
- ⚠️ Fixing same files repeatedly → not using correct formatter version
- ⚠️ Tests pass individually but fail in CI → missing imports or setup issues
- ⚠️ Black says "already formatted" but CI disagrees → wrong black version installed

### Version Pinning is Critical

**Always pin versions:**
- `.pre-commit-config.yaml`: Exact versions (e.g., `rev: 24.10.0`)
- `.github/workflows/ci.yml`: Exact versions (e.g., `black==24.10.0`)
- `requirements.txt`: Minimum versions with `>=` OR exact with `==`

**When updating formatter versions:**
1. Update `.pre-commit-config.yaml` first
2. Update `.github/workflows/ci.yml` to match
3. Run `pre-commit run --all-files` to reformat everything
4. Commit reformatted files
5. Update `requirements.txt` if needed
