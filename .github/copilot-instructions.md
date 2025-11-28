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
