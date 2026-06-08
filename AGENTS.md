# AGENTS.md — Working in the `creature` repo

This is the **canonical, cross-tool guide** for any AI agent (Claude Code, Cursor,
Codex, …) and for humans. `CLAUDE.md` and the Cursor rules both point here, so
keep this file as the single source of truth.

> **Golden rule:** a change is **not done** until the relevant gate is green —
> `cd back && make check` for backend changes, and the `npm run` gate for
> frontend changes (see below). Run it before you say you're finished.

---

## 1. What this project is

`creature` is a two-player, turn-based **card game**. Two parts:

| Path     | Stack                                                   | What it is |
| -------- | ------------------------------------------------------- | ---------- |
| `back/`  | Python 3.12 · FastAPI · SQLModel · PostgreSQL · Redis · `uv` | REST + WebSocket API and the **game engine** (a pure, event-driven rules pipeline) |
| `front/` | SvelteKit 2 · Svelte 5 · TypeScript · Vite 7 · BabylonJS · `npm` | Web client and 3D board |

The root [`README.md`](README.md) is the **game-rules specification** — the
functional/behaviour spec the engine implements. The backend talks to the
frontend over an OpenAPI contract and a WebSocket protocol.

## 2. Repo map & where to read next

| You want to… | Read |
| ------------ | ---- |
| Understand the system & module boundaries | [`docs/architecture.md`](docs/architecture.md) |
| Know every quality control & how to extend it | [`docs/harness.md`](docs/harness.md) |
| Work in the backend / engine | [`back/AGENTS.md`](back/AGENTS.md) + [`back/app/game/README.md`](back/app/game/README.md) |
| Work in the frontend | [`front/AGENTS.md`](front/AGENTS.md) |
| Contribute / open a PR | [`CONTRIBUTING.md`](CONTRIBUTING.md) |
| Coding style | [`.cursor/rules/`](.cursor/rules/) (fail-fast philosophy; Python DRY rules) |
| Plan a multi-step change | drop a plan in [`docs/exec-plans/active/`](docs/exec-plans/active/) |

## 3. Setup & run

```bash
# One-time: start Postgres 14 + Redis (Homebrew services)
make up                 # `make down` to stop

# Backend (http://localhost:8000, docs at /docs)
cd back && make install && make run

# Frontend (Vite dev server)
cd front && npm install && npm run dev
```
Backend config comes from `back/.env` (gitignored); every setting has a default
in `app/settings/config.py`, so the app boots without one. Pure engine tests need
no services.

## 4. The "done" gates (deterministic back-pressure)

Run the gate for the side you touched. **These must pass before a change is done.**

| Side | Command | Runs |
| ---- | ------- | ---- |
| Backend | `cd back && make check` | ruff (lint) · ruff format check · mypy · import-linter · pytest |
| Frontend (gating) | `cd front && npm run lint && npm run test && npm run deps:check && npm run build` | prettier + eslint (ratcheted) · vitest · dependency boundaries · build |
| Frontend (non-blocking) | `npm run check` | svelte-check — pre-existing type debt; run it, don't add new errors ([docs/harness.md](docs/harness.md)) |
| Running-app (core flows) | `cd front && npm run test:e2e` | Playwright real-browser smoke over the full stack — auth flow `@gating`, game-start + 3D `@nongating` ([front/AGENTS.md](front/AGENTS.md)). Run if you touched auth, lobby, game-start, or the 3D board |
| Both | `make check` (repo root) | fans out to backend + frontend |

Local hooks run the fast subset on every commit (see `.pre-commit-config.yaml`);
CI runs the full gate on every PR. Don't bypass these — fix the design instead.

## 5. Architecture rules you must respect

- **The game engine (`back/app/game/`) is pure and stateless.** It must never
  import persistence, web, auth, or service code. This is enforced by
  import-linter (`make arch`). If it fails, you crossed a boundary — fix the
  design, don't widen the allow-list.
- **Imports point downward.** Models/types → engine → services/websocket →
  routers. Known exceptions are documented in `pyproject.toml`
  (`[tool.importlinter]`) and [`docs/architecture.md`](docs/architecture.md).
- **Never hand-edit generated code:** `front/src/lib/api/*.gen.ts` and
  `front/src/lib/utils/generated/*`. Change the backend, then run
  `cd front && npm run generate`.

## 6. Common recipes

- **Add a backend Action / Event / Effect:** see [`back/AGENTS.md`](back/AGENTS.md).
- **Add an API endpoint:** add the route under `back/app/routers/`, regenerate the
  frontend client (`cd front && npm run generate`).
- **Write a test:** backend unit tests go in `back/tests/unit/` (no DB; use the
  `empty_state` / `place_card` fixtures in `back/tests/conftest.py`);
  DB-backed tests go in `back/tests/integration/` behind the `integration` marker.

## 7. Observability (for reproducing bugs)

- Structured logs: set `LOG_JSON=true` for JSON; every line carries a
  `correlation_id` (HTTP) or `room_id`/`game_id` (WebSocket).
- Metrics: `GET /metrics` (Prometheus).
- Tracing: set `OTEL_ENABLED=true` to print spans to the console (or set
  `OTEL_EXPORTER_OTLP_ENDPOINT` to export). See [`docs/references/observability.md`](docs/references/observability.md).

## 8. Commits & PRs

- Branch off `main`; never commit straight to `main`. The team uses **Graphite**
  for stacked PRs.
- Conventional-commit style subjects (`feat:`, `fix:`, `chore:`, `docs:`, …).
- Keep PRs small and gate-green. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## 9. When you're stuck

1. Re-read the relevant scoped guide (`back/AGENTS.md` / `front/AGENTS.md`) and
   [`docs/architecture.md`](docs/architecture.md).
2. Run the gate to see the exact failing sensor; read its message — it usually
   names the fix.
3. For engine behaviour, run the smoke test (`back/tests/unit/test_engine_smoke.py`)
   and turn on `LOG_LEVEL=DEBUG`.
4. If a control is wrong or missing, that's a harness bug — fix the control (and
   note it in [`docs/harness.md`](docs/harness.md)), don't just route around it.
