# GitHub Copilot Instructions

General guidance for AI assistants working on this project.

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

## Writing Style

Use British spellings and punctuation conventions:
- "colour" not "color"
- "optimise" not "optimize"
- "behaviour" not "behavior"
- Single quotes for emphasis where appropriate
- No em-dash (—), use standard British punctuation

**Tone and voice:**
- Clear, precise, technical writing
- Write in the style of Alan Turing and Stephen Hawking
- Some wry humour is acceptable
- Don't over-hype or make marketing claims
- Limited use of emojis (prefer none unless contextually appropriate)

**Avoid "AI tells":**
- Don't use rhetorical devices like "it's not just X, it's Y and Z"
- Avoid artificially enthusiastic language
- No superlatives unless factually justified
- Be direct and matter-of-fact

**Examples:**

✅ Good:
```
The weather client fetches current conditions from OpenWeatherMap. 
It handles API errors gracefully and caches responses for 10 minutes.
```

❌ Avoid:
```
Our amazing weather client doesn't just fetch data—it intelligently 
caches responses and gracefully handles errors! 🎉
```

## Code-Specific Standards

For Python code standards (formatting, linting, testing), see [python-standards.instructions.md](python-standards.instructions.md).
