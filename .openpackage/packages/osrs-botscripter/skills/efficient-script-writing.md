---
name: efficient-script-writing
description: Write, refactor, or review Python scripts for efficient, readable, and scalable automation. Use for any Python scripting work, especially when adding or upgrading a bot in Auto-OSBC, or when improving performance, maintainability, or structure.
---

# Efficient Script Writing

## Overview

Produce Python scripts that are easy to read, fast enough, and safe to scale. Apply this skill by default for all bot additions or upgrades.

## Quick Start

- Clarify purpose, inputs/outputs, and constraints (timing, safety, dependencies).
- Identify boundaries: pure logic vs. side effects (I/O, UI, network, file system).
- Sketch the minimal structure: entrypoint, config, core logic, adapters.
- Choose patterns from `references/python-script-patterns.md` when structure or performance is unclear.
- Implement in small, testable units; keep state explicit.

## Bot Upgrade Workflow (Required)

1. Map the behavior change in terms of states, triggers, and side effects.
2. Preserve existing human-behavior timing/randomization and detection boundaries.
3. Isolate new logic in a small module or class; keep I/O at the edges.
4. Add or update configuration for tunables instead of hardcoding constants.
5. Add logging or metrics for the new decision points.

## Structure Guidelines

- Use a clear entrypoint (`main` or a top-level class) that wires dependencies.
- Keep config and constants in one place; avoid hidden globals.
- Model state explicitly (enum or dataclass) and keep transitions centralized.
- Prefer pure functions for decision logic; keep side effects in adapters.

## Readability Guidelines

- Use descriptive names and small functions (single responsibility).
- Avoid deep nesting; prefer early returns and guard clauses.
- Use type hints for public functions and key data structures.

## Performance Guidelines

- Avoid tight loops; use sleep/backoff with jitter for polling.
- Cache stable computations and reuse expensive objects.
- Use `time.monotonic()` for timeouts and elapsed time.

## Scalability Guidelines

- Keep module boundaries clean to support future features.
- Make policies configurable (timings, thresholds, templates).
- Prefer dependency injection for external services and bot adapters.

## Quality Checklist (Run Before Finalizing)

- Script structure is obvious without reading all functions.
- State transitions are explicit and testable.
- Timing/randomization behavior is preserved for bots.
- Logging covers new branches and failures.
- Performance hotspots are avoided or isolated.

## References

- Read `references/python-script-patterns.md` for concrete layouts, patterns, and code templates.
