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
| **pytest** (behaviour, syrupy goldens) | backend | `make test` | CI — gating |
| **vulture + deptry** (dead code · dep drift) | backend | `make deadcode` | CI — gating |
| **mutmut** (mutation, engine) | backend | `mutmut run` | nightly (`mutation.yml`) — non-gating |
| **vitest** | frontend | `npm run test` | CI — gating |
| **dependency-cruiser** (boundaries) | frontend | `npm run deps:check` | CI — gating |
| **build** | frontend | `npm run build` | CI — gating |
| **eslint + prettier** | frontend | `npm run lint` | pre-commit · CI — gating (eslint ratcheted) |
| **svelte-check** | frontend | `npm run check` | CI — non-blocking (pre-existing type debt) |
| **tsc over `front/e2e/`** (specs vs the `window.__creature` contract) | frontend | `npm run check:e2e` | CI — gating (clean) |
| **knip** (dead code · unused exports/deps) | frontend | `npm run knip` | CI — non-blocking (baseline) |
| **Playwright E2E** (running-app smoke, real browser) | frontend + backend (full stack) | `npm run test:e2e` | CI (`e2e` job) — auth flow `@gating`; game-start + 3D-board + gameplay flows (play_card / pass / swap / attack) `@nongating` |
| **markdown link-check** | docs | `lychee --offline` | CI (`docs.yml`) |

The backend "done" gate is composed as **`make check`**. The frontend "done" gate
is **`npm run lint && npm run check:e2e && npm run test && npm run deps:check &&
npm run build`**.
`npm run lint` gates: prettier is clean and eslint is "ratcheted" — high-volume
legacy rules (`no-at-html-tags`, `require-each-key`, `no-explicit-any`,
`no-navigation-without-resolve`, …) are **warnings**, so the gate blocks new
*errors* while the backlog shows as warnings; don't add new violations. `npm run
check` (svelte-check) stays non-blocking until its pre-existing type debt is cleared.

The **Playwright E2E** sensor is the only **running-app** control: it boots the
whole stack (Postgres · Redis · backend · the production frontend build) and
drives a real Chromium through the core flows — login → lobby (`@gating`), a
two-browser game-start with the 3D board rendering, and deeper gameplay
(play_card, pass, swap, attack) (`@nongating`). It is what
makes [`front/AGENTS.md`](../front/AGENTS.md)'s "exercise BabylonJS / 3D through
the running app instead" instruction executable, and its deterministic
`[data-scene-ready]` board-ready signal is the probe a future autonomous loop
will poll. Gameplay is made testable by two enablers: a **seeded backend RNG**
(`GAME_SEED` → a per-game `random.Random`, keeping `app.game` pure) so the deal
and turn order reproduce, and a **build-gated `window.__creature` test API**
that reads `GameStateStore` and drives actions through the real
`ActionBuilder → GameConnection.sendAction` path (tree-shaken out of normal
builds; on only when `PUBLIC_E2E_HOOKS=1`). That API's surface is declared once
in an import-free contract
(`front/src/babylon-editor/src/scripts/devtools/e2e-contract.ts`) that the
in-page implementation and the Playwright specs both compile against —
`npm run check:e2e` gates it, since the specs sit outside the SvelteKit
tsconfig and are otherwise never type-checked. One real-pointer smoke
(`scene.pick` via `page.mouse.click`) covers the input chain the API skips.
Split gating follows the repo's ratchet pattern: the cheap, stable
auth flow blocks merges now; the flakier WebGL/gameplay flows run
`continue-on-error` until they settle, then get promoted. Specs live under
`front/e2e/*.e2e.ts`; see `front/playwright.config.ts` and the design plans in
`docs/exec-plans/completed/e2e-verification-harness.md` (game-start) and
`docs/exec-plans/completed/e2e-gameplay-harness.md` (gameplay).

### Architecture-fitness sensors (structural)

`back/pyproject.toml → [tool.importlinter]` turns invariants into tests:

1. **Game engine stays pure** — `app.game` may not import persistence, web, auth,
   or service code. (The crown-jewel guard.)
2. **Models do not import application machinery.**
3. **Layered architecture** — dependencies point downward only
   (`routers | websocket → services → game → auth → database → models → utils`).
4. **WebSocket internals stay layered** — within `app.websocket`, the chain
   `session → message_router → game_runner → lobby → room_registry → connections`
   points downward only.

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

The **running-app sensor gap is now closed**: until the Playwright E2E harness
landed, every sensor was static or unit-level and nothing exercised the app
actually running in a browser — a change could pass the whole "done" gate and
still leave login broken or the 3D board failing to render. That was the last
missing sensor *class*, and closing it (plus the deterministic board-ready
probe) is the prerequisite for the autonomous / long-running mode that pushes
the harness toward H3.

## The steering loop

The harness is owned and evolved like code: **when an issue recurs, improve the
control, don't just fix the instance.** A new class of bug → add a sensor (a test,
a lint rule, a boundary contract). A repeated misunderstanding → improve a guide
(`AGENTS.md`, a `references/` note, a `.cursor` rule). Coding agents make new
controls cheap to build — use them.

## Follow-up rungs (toward H3)

Tracked here so they're visible, not lost:

- **Backend type coverage** — `auth`, `database`, `utils`, `routers`,
  `models.db`, and `models.schemas` are now type-checked; `services`, `websocket`,
  and `settings` still carry `ignore_errors` (dynamic SQLAlchemy/async patterns).
  Drop those next; eventually `disallow_untyped_defs`.
- **Frontend type debt**: `npm run lint` (prettier + ratcheted eslint) now gates
  in CI and pre-commit. Remaining: ~55 `svelte-check` type errors (incl.
  `babylon-editor/src` and active routes) — clear them, then promote
  `npm run check` to gating too.
- **Tune `knip`**: the frontend dead-code/unused-exports sensor runs as a
  non-blocking baseline (it surfaces some genuinely dead app/legacy files) —
  triage and clear it, then promote `npm run knip` to gating.
- **Activate the Claude PR-review workflow** (add the API-key secret).
- **Promote the E2E game + 3D + gameplay flows (`@nongating` → `@gating`)** once
  they prove stable in CI — the next ratchet step for the running-app sensor.
  ~~deeper gameplay flows (play a card, end a turn, resolve an attack)~~ ✅ done
  (`docs/exec-plans/completed/e2e-gameplay-harness.md`). Remaining: widen
  coverage to cross-browser (WebKit) and a mobile viewport, and extend the
  screenshot baseline to canonical post-action states.
- **HUD → Svelte/DOM migration** (a *separate* future exec-plan): the action
  buttons / phase indicator / attack picker / turn banner are still drawn
  in-canvas (Babylon GUI), so gameplay specs drive their *actions* via the
  `window.__creature` API rather than clicking DOM. Once they move to DOM,
  assert them with `getByRole` and drop the corresponding test-API reliance
  (plus the accessibility/i18n payoff).
- **Wire the E2E harness in as the running-app verifier for autonomous mode**
  (the `[data-scene-ready]` / `creature:scene-ready` signal becomes the agent's
  "is it alive?" probe; the seeded deal + `window.__creature` extend it to an
  "is it *playing*?" probe).
