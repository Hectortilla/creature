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
  └─ app.routers | app.websocket ← HTTP + WebSocket entry points
       └─ app.services           ← business logic / orchestration
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

`back/pyproject.toml → [tool.importlinter]` (run with `make arch`) encodes three
contracts as deterministic tests:

1. **Game engine stays pure** — `app.game` must not import `app.routers`,
   `app.services`, `app.websocket`, `app.database`, `app.auth`, or `app.models.db`.
2. **Models do not import application machinery** — `app.models` must not import
   `app.routers`, `app.services`, `app.websocket`, or `app.auth`.
3. **Layered architecture** — dependencies point downward only across
   `routers | websocket → services → game → auth → database → models → utils`.

### Known debt (documented exceptions)

One upward edge remains, accepted and kept **visible** via `ignore_imports`:

| Edge | Why it exists | Status |
| ---- | ------------- | ------ |
| `app.models.game.state → app.game.effects` | lazy, function-local import that breaks an import cycle | kept function-local |

The earlier upward edges have been removed: `GameRoom` now lives in `app.models.game`
(not the websocket package), player-state assembly moved off the `User` model into
`app.services.player_state`, and auth looks up users directly instead of via a service.
With those gone, the layered contract above is enforced.

## Frontend structure

SvelteKit app under `front/src`: `lib/api/` (generated client + wrappers),
`lib/stores/`, components, and `routes/` (including the BabylonJS board and the
embedded `babylon-editor/`). Module boundaries within `src/lib` are enforced by
`front/.dependency-cruiser.cjs` (`npm run deps:check`). See
[`../front/AGENTS.md`](../front/AGENTS.md).
