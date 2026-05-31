# Architecture

How `creature` is structured and the dependency rules that keep it that way. For
the control-by-control view see [`harness.md`](harness.md); for the engine's
internals see [`../back/app/game/README.md`](../back/app/game/README.md).

## System overview

```
┌────────────────────┐         OpenAPI (REST)          ┌──────────────────────┐
│  front/ (SvelteKit) │ ──────────────────────────────▶│  back/ (FastAPI)     │
│  Svelte 5 · Babylon │ ◀───────  WebSocket  ──────────│  REST · WS · engine  │
└────────────────────┘    (real-time game protocol)    └──────────┬───────────┘
                                                                    │
                                                        Postgres 14 · Redis
```

- The frontend's API client is **generated** from the backend's OpenAPI schema
  (`npm run generate-client`) plus action metadata (`npm run generate-action-metadata`).
  Generated files (`front/src/lib/api/*.gen.ts`, `front/src/lib/utils/generated/*`)
  are **never hand-edited** — change the backend and regenerate. This is the
  contract boundary between the two halves.
- The root [`README.md`](../README.md) is the behaviour spec the engine implements.

## Backend layers

Dependencies point **downward**; higher layers may use lower ones, never the
reverse.

```
app.main                         ← FastAPI app, wiring, observability setup
  └─ app.routers                 ← HTTP endpoints
       └─ app.websocket | app.services | app.settings.admin
            └─ app.game          ← the game engine (pure, stateless)
                 └─ app.auth
                      └─ app.database
                           └─ app.settings.config
                                └─ app.models.db | app.models.schemas
                                     └─ app.models.game     ← engine data types
                                          └─ app.models.base | app.models.core
                                               └─ app.utils
```

### The game engine (`app.game`)

A stateless, event-driven pipeline:

```
Action → Validator → action.to_events() → EventLoop → Reducer → new GameState
```

It operates only on in-memory game data (`app.models.game`) and emits events; it
performs no I/O. This purity is what lets the whole rules system be unit-tested
without a database and reasoned about deterministically. See
[`../back/app/game/README.md`](../back/app/game/README.md) and
[`../back/AGENTS.md`](../back/AGENTS.md).

## Enforced boundaries

`back/pyproject.toml → [tool.importlinter]` (run with `make arch`) encodes two
contracts as deterministic tests:

1. **Game engine stays pure** — `app.game` must not import `app.routers`,
   `app.services`, `app.websocket`, `app.database`, `app.auth`, or `app.models.db`.
2. **Models do not import application machinery** — `app.models` must not import
   `app.routers`, `app.services`, `app.websocket`, or `app.auth`.

### Known debt (documented exceptions)

These are real upward edges that exist today, listed in `ignore_imports` so they're
**visible** rather than hidden. New violations beyond these fail CI. Each should be
removed over time (tracked in [`harness.md`](harness.md)):

| Edge | Why it exists | Fix |
| ---- | ------------- | --- |
| `app.game.engine → app.websocket.models` | `GameRoom` (the room/state container) lives in the websocket package | Move `GameRoom` into `app.models.game` |
| `app.models.game.state → app.websocket.models` | same `GameRoom` type | same |
| `app.models.db.user → app.services.decks` | a DB model builds player state via a service | Move that logic out of the model into a service |
| `app.models.db.user → app.websocket.serialization` | same | same |
| `app.auth.dependencies → app.services.users` | auth looks up users via a service | Acceptable, or invert via a thin repository |
| `app.models.game.state → app.game.effects` | lazy, function-local import to break a cycle | keep function-local |

A full top-to-bottom layered contract is deferred until the upward edges above are
removed (see [`harness.md`](harness.md) follow-ups).

## Frontend structure

SvelteKit app under `front/src`: `lib/api/` (generated client + wrappers),
`lib/stores/`, components, and `routes/` (including the BabylonJS board and the
embedded `babylon-editor/`). Module boundaries within `src/lib` are enforced by
`front/.dependency-cruiser.cjs` (`npm run deps:check`). See
[`../front/AGENTS.md`](../front/AGENTS.md).
