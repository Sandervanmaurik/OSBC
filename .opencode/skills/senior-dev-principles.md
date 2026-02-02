# Skill: Senior Developer Principles

## Core Principle
Keep code simple, readable, and separated by responsibility.

## Default Workflow

1. Clarify the requirement and constraints
2. Map responsibilities and boundaries
3. Choose the simplest design that works
4. Implement in small, testable steps
5. Review for readability and separation
6. Verify tests and quality gates

## Separation of Concerns Checklist

- Bot classes orchestrate flow; they do not embed detection details
- Visual detection lives in helpers/utilities, not UI code
- State evaluation is pure when possible (no I/O side effects)
- Configuration stays in options and is validated once
- Logging and error handling are centralized, not duplicated

## Readability Checklist

- Functions are short and named for intent
- Use early returns to reduce nesting
- Prefer explicit names over clever one-liners
- Comment only for "why" or non-obvious tradeoffs

## Complexity Guardrails

- Avoid new abstractions until 3+ call sites
- Prefer composition over inheritance
- Use small data objects for shared state
- Keep modules focused and small

## Testing Guidance

- Test behavior, not implementation details
- Isolate randomness with seeds or injected functions
- Use fixtures for visual states and templates
- Add regression tests for bug fixes

## Definition of Done

- Requirement met with minimal code
- Separation of concerns is clear
- Tests and checks pass
- No dead code or unused paths
