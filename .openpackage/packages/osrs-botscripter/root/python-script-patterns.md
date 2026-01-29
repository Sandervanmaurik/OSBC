# Python Script Patterns

Use these patterns when you need a clear, reusable structure or when performance/readability tradeoffs are unclear.

## Minimal Script Skeleton

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import logging
import time


@dataclass(frozen=True)
class Config:
    tick_seconds: float = 0.5
    max_idle_seconds: float = 10.0


def setup_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def load_config() -> Config:
    return Config()


def decide_action(state: str) -> str:
    if state == "idle":
        return "scan"
    return "noop"


def run_loop(cfg: Config) -> int:
    start = time.monotonic()
    while time.monotonic() - start < cfg.max_idle_seconds:
        action = decide_action("idle")
        logging.info("action=%s", action)
        time.sleep(cfg.tick_seconds)
    return 0


def main() -> int:
    setup_logging()
    cfg = load_config()
    return run_loop(cfg)


if __name__ == "__main__":
    raise SystemExit(main())
```

## State Machine Pattern

- Use an enum or string constants for states.
- Centralize transitions in one function or method.
- Keep guard conditions explicit and testable.

```python
from enum import Enum, auto


class State(Enum):
    IDLE = auto()
    SCAN = auto()
    ACT = auto()


def next_state(state: State, can_act: bool) -> State:
    if state == State.IDLE:
        return State.SCAN
    if state == State.SCAN and can_act:
        return State.ACT
    return State.IDLE
```

## Timing and Backoff

- Use `time.monotonic()` for elapsed time.
- Add jitter to reduce detection and improve responsiveness.

```python
import random
import time


def sleep_with_jitter(base: float, jitter: float) -> None:
    time.sleep(base + random.uniform(0.0, jitter))
```

## Performance Patterns

- Cache expensive pure functions.
- Batch repeated operations when possible.

```python
from functools import lru_cache


@lru_cache(maxsize=256)
def expensive_lookup(key: str) -> str:
    return key.upper()
```

## Readability Patterns

- Keep functions short and focused.
- Use early returns to avoid deep nesting.
- Prefer dataclasses for structured data.

## Scalability Patterns

- Separate core logic from adapters (I/O, UI, filesystem).
- Make thresholds configurable instead of hardcoded.
- Use dependency injection for external services.
