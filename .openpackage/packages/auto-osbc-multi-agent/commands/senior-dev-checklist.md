# Senior Developer Checklist

## Quick Review Questions

- Is each function doing one job?
- Are side effects isolated?
- Is naming clear without comments?
- Are edge cases handled?
- Did we add or update tests?

## Quality Gates

```bash
# Tests
pytest

# Lint
flake8 src/

# Types
mypy src/
```

## Optional Hygiene

```bash
# Run pre-commit hooks if configured
pre-commit run -a
```

## Small Refactor Moves

- Extract a pure helper for logic
- Move I/O to the outer layer
- Replace nested conditionals with early returns
- Replace duplication with a shared helper
