# AGENTS.md — `back/` (FastAPI + game engine)

Scoped guide for the Python backend. The canonical, repo-wide guide is the root
[`../AGENTS.md`](../AGENTS.md); read it first.

> **Golden rule:** `make check` must pass before a backend change is done. The
> game engine (`app/game/`) is a **pure, stateless, event-driven** pipeline —
> keep it free of I/O, DB, web, and service imports.

---

## Setup

- Python 3.12, package manager **`uv`** (`pyproject.toml`, `uv.lock`).
- `make install` (`uv sync`) to set up the venv.
- Config: `app/settings/config.py` (`Settings`). All values have defaults, so the
  app imports/boots without a `.env`. Postgres + Redis are only needed for
  `make run` and integration tests — **not** for engine/unit tests.

## Commands

| Intent | `make` target | Underlying |
| ------ | ------------- | ---------- |
| Run dev server | `make run` | `uv run uvicorn app.main:app --reload` |
| Lint | `make lint` | `uv run ruff check app tests` |
| Auto-format & fix | `make format` | `ruff format` + `ruff check --fix` |
| Format check (CI) | `make format-check` | `ruff format --check` |
| Type-check | `make typecheck` | `uv run mypy app` |
| Architecture boundaries | `make arch` | `uv run lint-imports` |
| Unit tests | `make test` | `uv run pytest -m "not integration"` |
| Tests + coverage | `make test-cov` | adds `--cov=app` |
| **Full gate ("done")** | **`make check`** | lint + format-check + typecheck + arch + test |

## Engine mental model

The engine is a stateless pipeline (full reference: [`app/game/README.md`](app/game/README.md)):

```
Action → Validator → action.to_events() → EventLoop → Reducer → new GameState
```

- `engine.py` — orchestrates validate → events → loop; returns `ActionResult`.
- `validators.py` — rule checks; returns `ValidationResult`.
- `actions/` — one class per action (`base.py` defines `Action`; `__init__.py`
  registers them in `ACTION_TYPES`). Actions implement `validate`, `to_events`,
  and `get_valid`.
- `event_loop.py` — applies events via the reducer, fans out triggered effects,
  auto-advances phases. Has safety caps (`max_iterations=1000`, `max_auto_advance=14`).
- `reducer.py` — pure event→state handlers (`@_handler(SomeEvent)`); mutate the
  passed `state`/`players` **in place** and return them.
- `effects.py` — the data-driven effect system (triggered + passive atoms).
- Events live in `app/models/game/events.py`; runtime state in `app/models/game/`.

## Module-boundary rules (enforced by `make arch`)

Direction: `models/* → game → services|websocket → routers → main`. Four contracts
(`pyproject.toml → [tool.importlinter]`):

1. **Engine purity** — `app.game` must not import `routers`, `services`,
   `websocket`, `database`, `auth`, or `models.db`.
2. **Model isolation** — `app.models` must not import `routers`, `services`,
   `websocket`, `auth`.
3. **Layered architecture** — app-wide dependencies point downward only
   (`routers | websocket → services → game → auth → database → models → utils`).
4. **WebSocket internals layered** — within `app.websocket`:
   `session → message_router → game_runner → lobby → room_registry → connections`.

The one documented exception is in `ignore_imports`: a lazy, function-local
`app.models.game.state → app.game.effects` import that breaks a cycle. **Do not add
to `ignore_imports` to silence a new violation** — fix the design, or raise it
explicitly. See [`../docs/architecture.md`](../docs/architecture.md).

## Recipes

**Add an Action**
1. Create `app/game/actions/<name>.py` subclassing `Action` (`actions/base.py`).
2. Implement `validate(state) -> ValidationResult`, `to_events(state) -> list[GameEvent]`,
   and `@classmethod get_valid(state, player_id) -> list[Action]`. Set `valid_phases`.
3. Register it in `ACTION_TYPES` in `app/game/actions/__init__.py`.
4. Add a unit test in `tests/unit/`.

**Add an Event**
1. Add the class to `app/models/game/events.py` (subclass `GameEvent`). It is
   auto-registered (the module derives `EVENT_TYPES`/`__all__` from one list).
2. Write a reducer in `app/game/reducer.py` decorated `@_handler(MyEvent)` — pure,
   mutate in place, return `(state, players)`.
3. If effects should react, map it in `event_loop.py` (`EVENT_TO_TRIGGER` or
   `_get_trigger_pairs`).

**Add an Effect atom**
1. Subclass `EffectAtom` in `app/game/effects.py` with a unique `atom_type`; set
   `default_triggers`/`passive_categories`; implement `execute()` (triggered) or
   `contribute_passive()` (passive).
2. **Add the class to `EFFECT_REGISTRY`** — it's built manually; a missing entry
   raises at `build_effect_atoms`. `test_registry_covers_every_atom_type` guards this.

## Gotchas / invariants

- Reducers **mutate in place** and return the same `(state, players)` — don't deep-copy.
- `process_action` catches all exceptions into `ActionResult.error`: a 200 response
  can still carry `success=False`. Always check `result.success`.
- `app.models.game.state` lazily imports `app.game.effects` inside a function to
  break a cycle — keep that import function-local.
- Known: two SAWarning relationship-overlap warnings on `Deck` fire at import
  (cleanup pending; that's why pytest `filterwarnings=error` is deferred).
- A pervasive `datetime.utcnow()` deprecation warning exists in model defaults
  (follow-up in [`../docs/harness.md`](../docs/harness.md)).

## Tests

- Unit tests (`tests/unit/`, marker `unit`): pure in-memory, no DB/Redis. Use the
  shared fixtures in `tests/conftest.py` (`empty_state`, `place_card`).
- Integration tests (`tests/integration/`, marker `integration`): need Postgres
  via the `db_session` fixture; excluded from `make test`, run in CI's integration job.

## mypy scope

mypy gates the **engine** (`app.game.*`, `app.models.game.*`) for bug-catching
errors. Framework code (routers/websocket/services/…) is not yet type-gated
(`ignore_errors` in `pyproject.toml`) — expanding that is a documented rung in
[`../docs/harness.md`](../docs/harness.md). New engine code should stay mypy-clean.
