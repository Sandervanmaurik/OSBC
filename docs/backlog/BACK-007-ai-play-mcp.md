# BACK-007: AI Plays OSRS via MCP (agentplay)

## Epic Overview
**Priority**: High
**Status**: Planned (no implementation yet). Plan agreed 2026-10-06.
**Dependencies**: None. Phase 0 cleanup comes first.

## Goal
An LLM agent plays OSRS through tool calls. **AI decides *what*, deterministic code does *how*.**
- The agent never sees or sends raw coordinates, and never chooses delays.
- All human-like behavior (CLAUDE.md rules) lives in the executor's `HumanPolicy`.
- So actions driven by the AI comply with those rules automatically.

## Decisions (confirmed)
| Topic | Decision |
|---|---|
| Topology | A single `osbc serve` daemon. It owns the window, one global input lock, the perception loop, the executor and the task runner. One localhost port serves MCP (streamable HTTP, `/mcp`), the dashboard (`/`) and a websocket (`/ws`). |
| Perception | Deterministic CV/OCR first, reusing the existing code. A cheap vision model (VLM) is used **only as a fallback**. |
| Brain | Staged. v1: an interactive Claude Code session attaches with `claude mcp add --transport http osbc http://127.0.0.1:<port>/mcp`. Later: the daemon supervises a headless agent runner. |
| Providers | Pluggable: an Anthropic adapter plus an OpenAI-compatible adapter (DeepSeek/OpenAI/Ollama). The VLM fallback uses the same abstraction. |
| Dashboard | Served by the daemon: static HTML + vanilla JS + websocket, no build step. Layout modelled on the "Railyard" reference. |
| Client mode | **RuneLite fixed mode only** in v1. |
| First scenario | **Woodcutting** (drop, then bank). Logic is ported from `src/model/osrs/woodcutter.py`, which stays unchanged. |
| Tag colors | Fixed convention: **trees = PINK, bank = GREEN**, NPCs = CYAN, ground items = PURPLE. |
| Item identity | OSRS Wiki sprites via `src/utilities/sprite_scraper.py`, matched by perceptual hash. Template match is the backup, and the VLM only handles unknowns. |
| Plugins | No custom RuneLite plugin. Existing plugins only (object/NPC tags, later Shortest Path). |
| Platforms | macOS (dev, possibly Retina) and Windows. |
| Deleted code | `src/model/actions` and `src/model/login` were removed intentionally. Don't restore them. The action layer is designed fresh. |

## Architecture
```
 Claude Code (v1)            Agent runner (later, in-process)
   │ MCP streamable HTTP        │ provider adapters (Anthropic | OpenAI-compatible)
   ▼                            ▼
┌──────────────────────── osbc serve (one process, one port) ──────────────────────────┐
│  /mcp ── MCP adapter ─┐                                                               │
│  /    ── dashboard ───┼─► ToolRegistry (9 tools) ─► SafetyGate ─► Executor ─► InputDriver
│  /ws  ── websocket ───┘        │   ▲ notices (chat, interrupts)        │      (Mouse/pyautogui)
│                                ▼   │                                  ▼
│                        TaskRunner ── EventBus ◄── WorldModel ◄── Perception ◄── FrameSource
│                                                   (stable IDs,     (extractors     (mss | Replay)
│  Stores: chat, bugs, action log + evidence          interrupts)     + VLM fallback) + CoordSpace
└───────────────────────────────────────────────────────────────────────────────────────┘
```

### Threading
- **Perception thread** (~2 Hz) takes no lock. It publishes the latest immutable `Snapshot` by swapping a reference.
- **Task worker**: one task at a time.
- **uvicorn asyncio loop**: serves MCP and the dashboard. Blocking tool handlers run via `anyio.to_thread.run_sync`.
- **Input lock**: one global `RLock`, held for a whole act sequence (acquire through postcondition).
- **Agent runner** (later): an asyncio task that calls the registry in-process.

## Package layout: `src/agentplay/`
| Dir | Contents |
|---|---|
| `domain/` | Frozen dataclasses: snapshot, targets, actions, events, results |
| `capture/` | `FrameSource` protocol, `MssSource` (one grab per tick), `ReplaySource` (replays `captures/` sessions), `CoordSpace` (**the only** place that converts pixels to points for DPI/Retina), `layout_fixed.json` plus a loader |
| `perception/` | Pure extractors (vitals, inventory, targets, chat, interface, hover, player_state) that wrap the legacy OCR/color/contour code on frame slices. Also `annotate.py` (set-of-mark), `phash.py`, `sprites.py` (index) and `vlm.py` |
| `world/` | Snapshot history, a target tracker with stable IDs, and interrupt rules `(prev, cur) -> events` (debounced) |
| `exec/` | `Executor`, `verify.py` (stages), `Expect`, `HumanPolicy`, `InputDriver`, `SafetyGate` |
| `tasks/` | `TaskRunner` plus built-ins: `gather` (woodcutting), `drop`, `bank` |
| `tools/` | A transport-agnostic `ToolRegistry` that holds the 9 tools |
| `adapters/` | `mcp_server.py`, `dashboard/` (http, ws, static), `providers/` (base, anthropic, openai_compat, pricing.json), `agent_runner.py` |
| `stores/` | Chat, bugs (`var/agentplay/bugs/*.json` plus evidence), action log |
| `legacy/` | The only modules allowed to import `src/utilities` or `src/model` |
| `app.py` | Composition root: `build_app(config)` |

Player memory files (outside `src/`): `agent/CLAUDE.md` (persona, rules, tools, tag colors), `agent/goals.md`, `agent/journal.md`.

**Changes to existing code**
- `src/cli.py`: add an `osbc serve` subcommand and remove the dangling imports.
- `src/model/bot.py:544/566`: remove the dangling imports.
- Dead tests: `tests/unit/actions`, `tests/unit/login`, the matching parts of `tests/unit/test_cli.py`, and `tests/e2e`.
- `src/utilities/action_watcher.py`: add "Woodcutting" to `KNOWN_ACTIONS`.
- `pyproject.toml`: add an optional extra `[agent]` with `mcp`, `starlette`, `uvicorn`, `anthropic`, `openai`, `pydantic`.

## Tool surface (9 tools)
| Tool | Input | Output |
|---|---|---|
| `observe` | `detail: brief\|full`, `image?: none\|scene\|inventory\|minimap`, `since?: seq` | `{seq, state, targets, diff?, image?}` |
| `act` | `do: click\|use_on\|press\|type\|drop\|select_menu`, `target?`, `with?`, `option?`, `expect?` | `ActionResult` |
| `start_task` | `name`, `params` | `{ok, task_id}` |
| `wait_for_event` | `timeout_s <= 60` | `{event, detail, state_diff}` |
| `stop_task` | `reason` | `{ok, final_state}` |
| `describe_scene` | `question?` | `{text, objects, cached, cost}` (VLM) |
| `say` | `text` | `{ok}`, which sends a message from the agent to the user |
| `report_bug` | `title`, `details`, `evidence?` | `{id}` |
| `memory` | `op: read\|append\|replace`, `file: goals\|journal`, `text?` | `{content}` |

- Every result carries `notices: [{type: chat|interrupt|bug_ack|stop_notice, ...}]`, so the agent never polls.
- Target IDs are valid for one `seq` only. A stale ID returns `{ok:false, reason:"stale_target", fresh_targets:[...]}`.
- Errors use a fixed stage enum (`acquire|hover|menu|click_check|postcondition`) and include a standard `suggestion`.
- Raw `debug_click(x, y)` exists only behind a config flag that is off by default.

### Snapshot (state about 400 tokens or less, diffs after the first call)
```json
{"seq":812,"hp":"43/60","pray":22,"run":81,"spec":null,
 "inv":{"used":23,"free":5,"items":["Logs x20","Bronze axe"]},
 "busy":"Woodcutting","chat_new":["You get some logs."],
 "targets":[{"id":"t1","kind":"object","label":"tree","color":"pink","dist":3}],
 "interface":null,"dialog":null,"warnings":[]}
```
- Targets are capped at 8, nearest first, plus a `more: n` count.
- Unknown sprites show as `"?sN"`.
- Internally each field is a `Reading{value, conf}`. A failing extractor degrades only its own field and adds a `warnings` entry.
- `SnapshotGameState` implements the existing `GameState` protocol from the snapshot.

## Executor verification ladder
1. **Re-acquire**: grab a fresh frame and resolve the target ID by IoU/centroid.
2. **Pick a point**: `HumanPolicy.pick_point` (`random_point`).
3. **Move**: the policy picks the speed. A misclick roll (8–15%) is corrected and logged as `policy`.
4. **Hover check**: OCR the hover text and its color class (yellow means NPC, cyan means object).
5. **Menu fallback** on mismatch: right-click, OCR the menu, select the option.
6. **Click and cross check**: a red cross means the interaction registered, yellow means a walk, and no cross triggers a refocus.
7. **Postcondition poll**: `Expect.kind` is one of `interface_open | inventory_delta | chat_contains | player_busy | target_gone`, with a timeout.

The result is `{ok, stage, reason, expected, observed, menu_options, retries, evidence:[paths], suggestion}`. The executor retries by itself (2 attempts) before escalating to the agent.

## Safety (`SafetyGate`; the agent has no tool to touch it)
- **Kill switch**: a dashboard button or global hotkey (default Ctrl+Alt+Shift+K) puts the daemon in `HALTED`. It resumes only from the dashboard or CLI (`osbc resume`), never via MCP.
- **Rate limits**: 40 inputs per minute (a token bucket with jitter, which delays rather than fails), 2 consecutive failures per target before escalating, 300 actions per task, a 2-hour session cap.
- **Refusals**: it refuses clicks outside the RuneLite window, when RuneLite is not focused, or when the client is **not in fixed mode**.
- **Lint test**: fails on `time.sleep(<literal>)` anywhere in `src/agentplay`.

## VLM fallback and token budget
- **Triggers**: an unknown interface for 2 frames, an unknown inventory sprite, or an explicit `describe_scene`. It is never called speculatively.
- **Output**: forced JSON (`kind`, `text`, `clickables`, `item_names`, `confidence`). Boxes are validated and converted to target IDs.
- **Cache**: dHash with Hamming distance ≤ 4. Sprites persist to `data/sprite_cache.json`; interfaces stay in memory for 10 minutes.
- **Budget**: per session, 30 calls or $0.50, with at least 5 s between calls for the same hash.
- **Agent tokens**: no images by default. Images are scaled to a long edge of 768 px or less at JPEG quality 70.
- **Prompt caching**: stable prefix order is system, then tools, then persona (cache breakpoint), then goals (breakpoint).
- **Trimming**: old observations are trimmed in chunks.
- **Target**: 15 or fewer LLM turns per 10 minutes of routine play.

## Agent runner (later)
- **Episode**: persona + goals + the last ~40 lines of the journal + the first `observe`.
- **Turn loop**: the stop flag is checked before every call and every tool.
- **Episode ends** on any of: 2 turns without tools, `max_turns=60`, context over 70% (summarize to the journal, then restart), or stop.
- **Crashes** restart with backoff, up to 3 times, then pause with an alert.
- **Meters** come from provider `usage`: context tokens, cache hit %, total tokens, cost (`pricing.json`), turn.

## Dashboard (Railyard-style; Map deferred)
**Panels**
- **Vitals**: state, world, HP bar, run, prayer, task. Coordinates and quest points show n/a for now.
- **Bug reports**: total / implemented / validated / closed, plus evidence crops.
- **Inventory grid**: equipment stubbed.
- **Agent Chat**: messages from the user are delivered as `notices`, and also raise `user_message` during `wait_for_event`.
- **Agent terminal**: tool log `> act {...}` / `< ok (ms)`. Start/Stop and meters arrive in phase 7.
- **Client stream**: MJPEG, with a toggle for the set-of-mark overlay.

**WS message types**: `hello`, `snapshot`, `frame`, `tool_call`, `tool_result`, `meters`, `chat`, `bug`, `task_event`, `runner_status`, `alert`, and `cmd` (client to server: `runner_start`, `runner_stop`, `kill`, `resume`, `chat_send`, `bug_status`).

## Woodcutting scenario
- **Phase 3 (agent drives each step)**: `observe` → `act(click, t1, expect=player_busy)` → wait → `act(drop ...)`.
- **Phase 4 (two-speed)**: `start_task("gather", {tag:"pink", item:"logs", on_full:"drop"|"bank", max_minutes})`.
  - Interrupts: `inv_full`, `unexpected_idle`, `low_hp`, `user_message`, `done`.
  - Banking uses the green tag and the bank-interface OCR already in `woodcutter.py`.
- **Busy/idle signal**: comes from `ActionWatcher` (with "Woodcutting" added), plus an inventory or XP delta as a second signal. Don't use `is_player_idle_visual`, which always returns True.

## Item sprites
- `osbc sprites sync --set woodcutting` downloads logs (all tiers), bronze through rune axes, bird nests and so on through `sprite_scraper.py`.
- It builds `sprite_index.json`, which maps phash to name.
- **Extractor order**: phash lookup, then template match (`crop_bottom_portion=0.7` to skip stack text), then `"?sN"` for the VLM queue.

## Phases and exit criteria
| # | Phase | Exit criterion |
|---|---|---|
| 0 | Remove dangling `actions`/`login` imports and dead tests | `pytest -m "not slow"`, mypy and flake8 are green, and `osbc --help` works |
| 1 | `MssSource`/`ReplaySource`, `CoordSpace`, `layout_fixed.json`, fixed-mode guard | Slices of a recorded frame match the live `Window` rects, scale-1 and scale-2 tests pass, and there is one grab per tick |
| 2 | Extractors, snapshot, `osbc sprites sync`, sprite index, ActionWatcher "Woodcutting" | ≥95% field accuracy and correct slot names on woodcutting fixtures, under 100 ms per extractor, state under 400 tokens, and busy/idle correct on a replayed chop |
| 3 | Executor, `SafetyGate`, `osbc serve`, MCP (`observe`/`act`) | **Claude Code chops a pink tree and drops the logs using only tools.** 20 of 20 verified clicks hit, a stale ID gives `stale_target`, and the kill takes 300 ms or less |
| 4 | Task runner, `wait_for_event`, chat, bugs, `say`/`report_bug`/`memory` | 10 minutes of unattended woodcutting (drop and bank) in 20 or fewer turns, a chat message interrupts the task, and a bug file is written with evidence |
| 5 | Dashboard | All panels are live, the stream runs at 5 fps or better, chat round-trips, and the kill button halts |
| 6 | VLM fallback and sprite cache | Over 80% cache hits on a replay, caps enforced, and at least 90% correct unknown-sprite naming on fixtures |
| 7 | Headless runner, providers, meters, terminal Start/Stop | The same scenario runs headless, the provider can be switched through config, meters match provider usage, and crash restart works |
| 8 | Navigation (world map + Shortest Path minimap line) and the Map panel | Later. First investigate a coordinate-overlay plugin |

## Testing
- **Spec first**: `tests/specs/agentplay-*.spec.md`.
- **Unit**:
  - domain round-trips
  - `CoordSpace` property tests at scale 1 and 2
  - interrupt rules over snapshot pairs
  - the executor with `FakeInputDriver`, `FakeClock` and a `ScriptedFrameSource` (per-stage failures, lock exclusion, varied delays)
  - registry schema checks, and a test that the MCP tool list equals the registry
- **Integration**:
  - golden frames (`tests/agentplay/fixtures/frames/*.png` with `.expected.json`, plus `meta.json` for scale and origin)
  - the MCP SDK in-memory client
  - the Starlette TestClient for the websocket
  - providers via recorded HTTP
- **Replay E2E**: `ReplaySource`, fake input, the full app and a scripted agent.
- **Live**: manual and marked slow, on Mac Retina and on Windows.

## Risks
1. **Retina/DPI**: `mss` uses physical pixels while pyautogui/pywinctl use points. Mitigated by `CoordSpace` as the only converter and early scale-2 tests.
2. **OCR fragility**: no spaces and flicker. Mitigated with fuzzy matching, debounce, confidence values and the VLM fallback.
3. **Wiki sprites vs in-game slots**: stack text and highlights. Measure in phase 2.
4. **Stable target IDs for moving targets**: the IDs are hints. Re-acquiring a fresh frame before each action is mandatory.
5. **Input lock deadlocks**: mitigated by lock timeouts, cooperative cancel and a watchdog.
6. **Legacy singletons** (`Mouse` class-level state, `BotSessionState`): confined to `legacy/`.
7. **MCP long-poll timeouts**: `wait_for_event` is capped at 60 s or less and returns heartbeats.
8. **macOS permissions** (Accessibility, Screen Recording): `osbc serve` runs a first-run check.

## Open items
- The coordinate-overlay plugin, for `where_am_i` and the Map panel (phase 8).
- Equipment perception (the dashboard panel is stubbed for now).
