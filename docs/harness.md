# The `creature` harness

This repo is built to be worked on by AI coding agents as much as by humans,
following the model in OpenAI's *[Harness engineering](https://openai.com/index/harness-engineering/)*:

> **Agent = Model + Harness.** The harness is the explicit scaffolding around the
> model — instructions, tools, verification, observability, and boundaries — that
> (a) increases the chance the agent gets it right the first time, and (b) gives a
> feedback loop that self-corrects most issues before a human sees them.

Two kinds of control:

- **Guides (feedforward)** steer *before* the agent acts — docs, conventions,
  types, configured boundaries.
- **Sensors (feedback)** catch problems *after* it acts — tests, linters, type
  checkers, structural tests, CI.

Each is **computational** (fast, deterministic) or **inferential** (slower,
semantic / AI). We "keep quality left": cheap checks run locally on every edit
and commit; fuller checks run in CI; the rest is monitored over time.

---

## Guides (feedforward) ✦

| Control | Kind | Where |
| ------- | ---- | ----- |
| Canonical agent guide | doc | [`/AGENTS.md`](../AGENTS.md) → `CLAUDE.md`, `.cursor/` point to it |
| Scoped guides | doc | [`back/AGENTS.md`](../back/AGENTS.md), [`front/AGENTS.md`](../front/AGENTS.md) |
| Architecture & boundaries | doc | [`architecture.md`](architecture.md) |
| Engine reference | doc | [`back/app/game/README.md`](../back/app/game/README.md) |
| Game-rules / behaviour spec | doc | [`/README.md`](../README.md) |
| Coding style (fail-fast; Python DRY) | guide | [`.cursor/rules/*.mdc`](../.cursor/rules/) |
| Library notes for LLMs | doc | [`references/`](references/) |
| Plan-tracking convention | process | [`exec-plans/`](exec-plans/) |
| Type system (the engine is fully typed) | computational | `back/` mypy-strict on `app.game.*` |
| Editor defaults | computational | `.editorconfig` |

## Sensors (feedback) ◎

### Computational — fast & deterministic

| Sensor | Scope | Command | Stage |
| ------ | ----- | ------- | ----- |
| **ruff** (lint) | backend | `make lint` | pre-commit · CI |
| **ruff format** | backend | `make format-check` | pre-commit · CI |
| **mypy** (engine-strict) | backend | `make typecheck` | CI (pre-push) |
| **import-linter** (boundaries) | backend | `make arch` | CI |
| **pytest** (unit) | backend | `make test` | CI |
| **pytest** (integration, Postgres/Redis) | backend | `pytest -m integration` | CI (services) |
| **vitest** | frontend | `npm run test` | CI — gating |
| **dependency-cruiser** (boundaries) | frontend | `npm run deps:check` | CI — gating |
| **build** | frontend | `npm run build` | CI — gating |
| **eslint + prettier** | frontend | `npm run lint` | CI — non-blocking (pre-existing debt) |
| **svelte-check** | frontend | `npm run check` | CI — non-blocking (pre-existing debt) |
| **markdown link-check** | docs | `lychee --offline` | CI (`docs.yml`) |

The backend "done" gate is composed as **`make check`**. The frontend "done" gate
is **`npm run test && npm run deps:check && npm run build`**; `npm run lint` and
`npm run check` run non-blocking for now because of pre-existing app/legacy debt
(see follow-ups) — don't add new violations.

### Architecture-fitness sensors (structural)

`back/pyproject.toml → [tool.importlinter]` turns invariants into tests:

1. **Game engine stays pure** — `app.game` may not import persistence, web, auth,
   or service code. (The crown-jewel guard.)
2. **Models do not import application machinery.**

Frontend: `front/.dependency-cruiser.cjs` enforces `src/lib` layering and forbids
cycles.

### Inferential — semantic / AI

| Sensor | Where | Status |
| ------ | ----- | ------ |
| Claude PR review | `.github/workflows/claude-review.yml` | **opt-in** — inert until an `ANTHROPIC_API_KEY` secret is added |
| On-demand `/code-review`, `/security-review` | Claude Code skills | available now |

---

## Observability (so agents can reproduce bugs)

- **Structured logs** (`structlog`): console in dev, JSON when `LOG_JSON=true`;
  correlation IDs via `asgi-correlation-id` (HTTP) and bound `room_id`/`game_id`
  (WebSocket). Setup: `back/app/settings/logging.py`.
- **Metrics** (`prometheus-fastapi-instrumentator`): `GET /metrics`.
- **Tracing** (OpenTelemetry): FastAPI auto-instrumented + an explicit
  `engine.process_action` span; console exporter in dev, OTLP when configured.
  Off by default (`OTEL_ENABLED`). Setup: `back/app/settings/observability.py`.

See [`references/observability.md`](references/observability.md).

---

## Maturity

Using the H0–H3 ladder from the article (H0 = model output only; H3 = full
structured reports + signed episode packages):

**Current target: H2** — deterministic checks gate "done", with failure
attribution (each sensor names what failed and usually how to fix it), full
local + CI back-pressure, and observability for reproduction.

## The steering loop

The harness is owned and evolved like code: **when an issue recurs, improve the
control, don't just fix the instance.** A new class of bug → add a sensor (a test,
a lint rule, a boundary contract). A repeated misunderstanding → improve a guide
(`AGENTS.md`, a `references/` note, a `.cursor` rule). Coding agents make new
controls cheap to build — use them.

## Follow-up rungs (toward H3)

Tracked here so they're visible, not lost:

- **Backend type coverage** beyond the engine (drop `ignore_errors` for
  routers/services/websocket; eventually `disallow_untyped_defs`).
- **Coverage ratchet**: set `fail_under` once a baseline is measured.
- **Enable pytest `filterwarnings=error`** after fixing the `Deck` relationship
  `SAWarning`s and the `datetime.utcnow()` deprecation.
- **Architecture debt**: move `GameRoom` from `app.websocket.models` into
  `app.models.game`; remove `models.db.user → services/websocket` and
  `auth → services` upward edges — then promote a full layered import contract.
- **Frontend lint/type debt**: clear the pre-existing prettier/eslint/svelte-check
  findings in app/legacy code (`npm run format`, then triage eslint + svelte-check),
  then promote `npm run lint` / `check` to gating and add them to pre-commit.
- **More sensors**: mutation testing, a dead-code/drift job, behaviour
  fixture-approval tests.
- **Activate the Claude PR-review workflow** (add the API-key secret).
