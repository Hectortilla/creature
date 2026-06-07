# Running-app verification harness (Playwright E2E)

> Status: **spec / not started** · Owner: _TBD_ · Target maturity: advances the
> harness from **H2 → H3** (see [`../../harness.md`](../../harness.md)).

A real-browser smoke harness that drives the **integrated, running** app
(frontend + backend + Postgres + Redis) through the core flows. This is the one
sensor class the harness is missing today.

---

## 1. Goal & why this exists

**Close the one true sensor gap.** Every sensor in
[`docs/harness.md`](../../harness.md) is static or unit-level — ruff, mypy,
import-linter, pytest, vitest, dependency-cruiser, build, eslint. **Nothing
exercises the app actually running in a browser.** A change can pass the entire
"done" gate and still leave login broken, the lobby unable to start a game, or
the 3D board failing to render. That blind spot is what this feature removes.

Three concrete payoffs:

1. **Makes [`front/AGENTS.md:136`](../../../front/AGENTS.md) executable.** That
   line instructs agents: _"Do not unit-test BabylonJS / 3D code; exercise that
   through the running app instead."_ Today there is no mechanism to "exercise
   through the running app." This builds it.
2. **Closes the sensor gap** in the harness sensor table — adds the first
   running-app (integration-level, real-browser) feedback control.
3. **Prerequisite for autonomous / long-running mode.** An agent working
   unattended needs a signal that answers "does the app still actually work?"
   the way a human would check — Anthropic's _"verify as a human."_ Without a
   running-app verifier there is no safe autonomy. This is that verifier.

This is **net-new**: there is no Playwright dependency, no `test:e2e` script, and
no E2E config in the repo today.

---

## 2. Scope

### In scope (v1)

- A `@playwright/test` setup under `front/` with a `playwright.config.ts` and a
  `test:e2e` script family.
- **Two smoke flows:**
  - **Auth smoke (gating):** login → home → lobby renders with a playable deck.
  - **Game smoke (non-gating):** two real browsers — A creates a room, B joins —
    both reach the in-game view and the **3D board renders**.
- An **optional, non-gating, masked screenshot baseline** of the 3D canvas.
- **Deterministic test-data seeding** (two users, each with a valid deck) via the
  public REST API.
- A small, deterministic **"board-ready" signal** in the app (also the hook the
  autonomous loop will poll later).
- A **CI job** that brings up the full stack and runs the flows, wired into the
  existing `ci-ok` aggregate with the **split gating** posture below.
- Harness/doc updates so the new sensor is registered and **owned like code**.

### Non-goals (v1)

- Full gameplay coverage (playing turns, attacks, win/lose) — **smoke only**.
- Cross-browser (WebKit / Firefox) — **Chromium only** for v1.
- Pixel-perfect, gating visual regression of the 3D layer.
- Replacing the backend integration tests (`pytest -m integration`).
- Mobile / responsive viewports.

---

## 3. Decisions (locked) & rationale

| # | Decision | Rationale | Alternative considered |
| - | -------- | --------- | ---------------------- |
| D1 | **Start a game with two real browsers** (context A creates a room, context B joins) | A game only starts when a room has **≥2 players** ([`back/app/models/game/room.py:91`](../../../back/app/models/game/room.py) — `game_ready_to_start`). There is **no AI/bot/single-player** mode; a single browser cannot start a game. Two browsers exercise the real join → auto-start path end-to-end. | A headless **WebSocket "sparring bot"** as player 2 (lighter, more stable). **Kept as the documented fallback** if two-browser proves too flaky (see §10). |
| D2 | **Roles/labels first; `data-testid` only as a deliberate fallback** | Playwright's own guidance + Testing-Library philosophy: query the app the way a user / assistive tech does, so tests survive refactors and catch a11y regressions for free. `data-testid` couples tests to implementation, so it's an escape hatch. | "`data-testid` everywhere" (brittle to markup, litters prod) or "existing CSS/`id`/text only" (no app edits, but fragile). |
| D3 | **Split gating:** the auth flow **gates**; the game-start + 3D flow is **non-gating** | Matches the repo's established ratchet pattern (knip, svelte-check land non-blocking then get promoted — [`ci.yml:116`](../../../.github/workflows/ci.yml), [`ci.yml:128`](../../../.github/workflows/ci.yml)). The cheap, stable auth path gives real back-pressure now; the flakier WebGL/two-browser path settles before it can block unrelated PRs. | Gate everything day one (flakes block the repo) or gate nothing (no back-pressure). |
| D4 | **3D screenshot baseline: include now, non-gating, masked + tolerance** | Gives a real signal on the 3D layer without the WebGL-determinism-in-CI rabbit hole blocking merges. Masking dynamic regions + a pixel tolerance keeps it useful, not noisy. | Defer entirely (no 3D signal) or gate it (fragile across GPUs/OS). |
| D5 | **Seed test data via the public REST API** in Playwright global-setup | No test-only backdoors → the tests stay honest and exercise the real endpoints. Unique users per run keep tests isolated and re-runnable against the persistent local DB. | A backend seed script / `make seed-e2e` (faster, but more surface to keep in sync) or a test-only seed endpoint (security smell). Seed script is noted as a later optimization (§10). |

---

## 4. What the app currently gives us (constraints baked into the design)

- **Routes:** login `/login`, register `/register`, home `/`, game lobby + board
  `/game` ([`front/src/routes/`](../../../front/src/routes/)). Auth is enforced;
  unauthenticated users are redirected to `/login`.
- **Login:** username + password → `POST /auth/token` → `GET /auth/me`; token
  stored in `localStorage["auth_token"]` (+ a `auth_token` cookie).
  ([`front/src/routes/login/+page.svelte`](../../../front/src/routes/login/+page.svelte),
  [`back/app/routers/auth.py:18`](../../../back/app/routers/auth.py)).
- **A fresh user has zero decks.** A deck is **valid for playing only at exactly
  22 cards** ([`back/app/models/game/state.py:62`](../../../back/app/models/game/state.py)).
  30 cards are seeded globally (IDs 1–30) by the initial migration. So each test
  player must be given a 22-card deck before they can start a game.
- **Starting a game** is auto-triggered when a second WebSocket client joins a
  room ([`back/app/websocket/session.py`](../../../back/app/websocket/session.py),
  [`game_runner.py`](../../../back/app/websocket/game_runner.py)).
- **The board** is a `<canvas>` inside `.scene-wrapper`, mounted by
  [`BabylonEditorScene.svelte`](../../../front/src/lib/components/BabylonEditorScene.svelte),
  with a `loading` state ("Loading scene…") that flips to `false` on success.
  **There are no `data-testid` attributes anywhere in the app today.**
- **CI already runs Postgres 14 + Redis 7** as service containers and applies
  Alembic migrations ([`ci.yml:58`](../../../.github/workflows/ci.yml)), with a
  `ci-ok` aggregate job for branch protection ([`ci.yml:132`](../../../.github/workflows/ci.yml)).

---

## 5. Design

### 5.1 Tooling & file layout

- Add `@playwright/test` (devDependency). Install Chromium only:
  `npx playwright install --with-deps chromium`.
- `front/playwright.config.ts`; specs live under **`front/e2e/`**.
- **Runner-collision guard (important):** Vitest and Playwright both match
  `*.spec.ts` / `*.test.ts`. Avoid the clash by:
  - naming E2E specs **`*.e2e.ts`** and setting Playwright `testDir: './e2e'`;
  - adding `e2e/**` to Vitest's `exclude` in `vitest.config.ts`.
- `front/e2e/` sits **outside `src/`**, so `npm run deps:check` (cruises `src`)
  is unaffected; confirm eslint includes/ignores it sensibly.

`package.json` scripts:

| Script | Purpose |
| ------ | ------- |
| `test:e2e` | run all flows (gating + non-gating) |
| `test:e2e:gating` | run only `@gating`-tagged specs (the CI blocking subset) |
| `test:e2e:ui` | Playwright UI mode (local debugging) |
| `test:e2e:headed` | headed run (local debugging) |
| `test:e2e:update-snapshots` | regenerate the 3D screenshot baseline |

### 5.2 Stack bring-up & server orchestration

The E2E run needs the **whole stack**: Postgres 14 · Redis 7 · `alembic upgrade
head` · backend (uvicorn `:8000`) · built frontend preview (`:4173`).

- **Frontend under test = the production build** (`npm run build && npm run
  preview`, port 4173), not the dev server — it's what the `build` sensor already
  produces and is closest to reality. `baseURL = http://localhost:4173`.
- **Backend** = `uv run python -m uvicorn app.main:app` on `:8000`. The frontend
  talks to it via `PUBLIC_API_URL` (default `http://localhost:8000`).
  - ✅ **Resolved (Step 1):** `PUBLIC_API_URL` is inlined at **build time** —
    `src/lib/api.ts` imports it from `$env/static/public`, so `npm run build`
    *fails* if it isn't set beforehand. The harness sets it via Playwright's
    `webServer.env` (default `http://localhost:8000`), so the preview build is
    self-sufficient even with no `front/.env` (e.g. CI).
- **Orchestration:** Playwright `webServer` (array form) launches **both** the
  backend and the frontend preview, with `reuseExistingServer: true` for local
  runs. Generous `timeout` for first-boot.
- **Prerequisites that `webServer` does _not_ own:** Postgres/Redis must be up
  and migrations applied. Locally: `make up` then `cd back && uv run alembic
  upgrade head`. In CI: service containers + an explicit migration step (§5.6).

### 5.3 Test-data seeding (global-setup)

`front/e2e/global-setup.ts` runs once before the suite and, for **each of two
players** (roles `host` and `guest`), via the **public REST API**:

1. `POST /auth/register` with a **unique** username, e.g. `e2e_host_<runId>` (a
   timestamp/uuid) → isolated and re-runnable on the persistent local DB.
2. `POST /auth/token` → JWT.
3. `POST /decks` → `deck_id`.
4. **22×** `POST /decks/{deck_id}/cards/{card_id}` (card IDs `1..22`).
5. Assert `GET /decks/{deck_id}.is_valid_for_playing === true`.

It then persists, per player:

- credentials + `deck_id` (for the auth flow's **real UI login**), and
- a **Playwright `storageState`** (logged-in `localStorage`/cookie) so the
  **game flow can skip the UI login** and start from the lobby — isolating the
  game/3D flow from any auth-UI flakiness.

~46 API calls once per run is acceptable. If it becomes a bottleneck, the
fallback is a backend seed script (§10).

### 5.4 App changes (kept minimal, and they pay double)

These are the only production-code edits, chosen to be the smallest set that
makes the flows robust — and each also serves the autonomous-mode goal:

1. **Deterministic board-ready signal.** When the Babylon scene finishes
   initializing (`loading=false`, render loop running) in
   [`BabylonEditorScene.svelte`](../../../front/src/lib/components/BabylonEditorScene.svelte),
   expose a stable signal — e.g. set `data-testid="game-board"` and
   `data-scene-ready="true"` on the scene container (and/or dispatch a
   `creature:scene-ready` window event). Tests await
   `[data-testid="game-board"][data-scene-ready="true"]` instead of scraping the
   "Loading scene…" text (brittle, i18n-fragile). **This is exactly the hook an
   autonomous verifier will poll.**
2. **`data-testid="game-board-canvas"`** on the `<canvas>` — a canvas has no
   accessible role/name, so this is the legitimate `data-testid` fallback (D2).
3. **Accessible login form.** Ensure the username/password inputs have proper
   `<label for>` so tests use `getByLabel(...)` and confirm the Sign-In button's
   accessible name — a small a11y win that falls straight out of D2.

Everything else is queried by **role / label / text** (no new test ids).

### 5.5 The two smoke flows

**Flow A — auth smoke · `e2e/auth.e2e.ts` · `@gating`** (DOM/role depth, no 3D):

1. `goto('/')` while unauthenticated → assert redirect to `/login`.
2. `getByLabel('Username'|'Password')` → fill seeded `host` creds → click the
   Sign-In button (`getByRole('button', { name: /sign in/i })`).
3. Assert landing on `/` (home).
4. Navigate to `/game`; assert the **"Game Lobby"** heading, and that the seeded
   deck is present and **selectable** (i.e. surfaced as valid for playing).
5. _(optional negative)_ bad credentials → assert the error message (prefer
   `role="alert"`; wiring that on `.error-message` is a tiny add).

**Flow B — game start + board render · `e2e/game.e2e.ts` · `@nongating`:**

1. Two browser contexts, `host` and `guest`, each loaded with its seeded
   `storageState`.
2. **host:** `goto('/game')` → select deck → **"Create New Room & Play."**
3. **guest:** `goto('/game')` → select deck → **"Join Existing Room"** → refresh
   the room list → pick the available room (`can-join`) → **"Join Room & Play."**
   - Room discovery is done **through the UI room list** (true two-browser
     fidelity). _Fallback_ if timing is flaky: capture the host's `room_id`
     (from URL / page state) and have the guest navigate with it directly.
4. **Both contexts:** assert transition to the in-game view ("Playing"), then
   assert `[data-testid="game-board"][data-scene-ready="true"]` is visible and
   the canvas has non-zero size.
5. _(optional, non-gating)_ `expect(canvas).toHaveScreenshot('board.png', {
   maxDiffPixelRatio: <tolerance>, mask: [<dynamic regions>] })`.

Use generous per-step timeouts for scene load; enable `retries` + `trace` in CI.

### 5.6 WebGL in headless CI

BabylonJS needs a WebGL2 context with no GPU present. Launch Chromium with
software rendering, e.g. `--use-gl=angle --use-angle=swiftshader` (and/or
`--enable-unsafe-swiftshader`) via `launchOptions.args` in the config. Confirm
Havok physics (WASM) initializes headless. The **non-gating** posture on Flow B
absorbs initial instability here while we tune it.

### 5.7 CI wiring (`.github/workflows/ci.yml`)

Add one **`e2e` job** (runs when `frontend` **or** `backend` changed — it
exercises both):

- **Services:** `postgres:14` + `redis:7`, reusing the existing pattern
  ([`ci.yml:58`](../../../.github/workflows/ci.yml)).
- **Steps:** checkout → setup-uv + Python 3.12 + `uv sync` → setup-node 22 +
  `npm ci` → `alembic upgrade head` → `npm run build` →
  `npx playwright install --with-deps chromium` → start backend → **two test
  steps** implementing the split:
  1. `npm run test:e2e:gating` — **blocking** (job fails on failure).
  2. `npm run test:e2e -- --grep @nongating` — `continue-on-error: true`
     (**non-blocking**), mirroring the knip/svelte-check rungs.
- **Artifacts (always):** `playwright-report/`, traces, screenshots, snapshot
  diffs.
- **Branch protection:** add the `e2e` job to `ci-ok`'s `needs`
  ([`ci.yml:132`](../../../.github/workflows/ci.yml)). Because the non-gating
  step is `continue-on-error`, a 3D-only failure leaves the job green and
  `ci-ok` green; only an **auth-flow** failure turns the job red and blocks the
  merge — exactly the D3 split.

> **Snapshot baselines** live committed under `front/e2e/` and must be generated
> in the **same environment** they're compared in (the CI Ubuntu image +
> swiftshader). Document `test:e2e:update-snapshots`; since the screenshot is
> non-gating, environment drift surfaces as a (non-blocking) diff rather than a
> blocked merge.

---

## 6. Execution queue (work orders)

Do these **in order**, one step per agent, per §0. Each step is sized to leave
the gate green and be shippable on its own.

> **Local prerequisite for any step that starts the backend (Steps 3–6):**
> `make up` (Postgres + Redis), then `cd back && uv run alembic upgrade head`.
> Steps 1–2 need no backend.

### Step 1 — Scaffold Playwright + a trivial running-app test

- [x] **Status:** ✅ done — 2026-06-07 — Playwright + Chromium scaffolded; `npm run test:e2e` smoke green; frontend gate green — commit `88aa872`
- **Depends on:** —
- **Goal:** prove the harness boots the built frontend and drives a real browser.
- **Do:**
  - Add `@playwright/test` (devDep); `npx playwright install --with-deps chromium`.
  - `front/playwright.config.ts`: chromium project; `testDir: './e2e'`,
    `testMatch: '**/*.e2e.ts'`; `baseURL: 'http://localhost:4173'`; `webServer` =
    **frontend preview only** (`npm run build && npm run preview`, port 4173,
    `reuseExistingServer: !process.env.CI`); chromium swiftshader
    `launchOptions.args` (§5.6); `retries: process.env.CI ? 2 : 0`;
    `trace: 'on-first-retry'`. **Do not** wire `globalSetup` yet.
  - `vitest.config.ts`: add `'e2e/**'` to `test.exclude`.
  - `package.json` scripts: `test:e2e`, `test:e2e:gating`, `test:e2e:ui`,
    `test:e2e:headed`, `test:e2e:update-snapshots` (§5.1).
  - `.gitignore`: `front/playwright-report/`, `front/test-results/`,
    `front/e2e/.auth/`.
  - `front/e2e/smoke.e2e.ts`: `goto('/login')` and assert the login form is
    visible. (A fresh context has no auth cookie, so no backend call should fire;
    if this app's `hooks.server.ts` *does* hit the backend on `/login`, defer
    this assertion to after Step 3 and assert a static route instead.)
- **Acceptance:** `npm run test:e2e` passes; the frontend gate stays green.
- **Verify:**
  ```bash
  cd front && npm run test:e2e
  cd front && npm run lint && npm run test && npm run deps:check && npm run build
  ```
- **Notes for next agent:**
  - `@playwright/test@1.60.0` added (devDep). Chromium installed with
    `npx playwright install chromium` (no `--with-deps`: that's a Linux/CI-only
    flag, a no-op on macOS). CI still uses `--with-deps` per Step 7.
  - **§5.2 RESOLVED — `PUBLIC_API_URL` is inlined at BUILD time** (`$env/static/public`
    in `src/lib/api.ts`). `npm run build` *fails* (`"PUBLIC_API_URL" is not exported`)
    if it isn't set first. The harness now sets it via Playwright `webServer.env`
    (default `http://localhost:8000`, overridable), so the preview build is
    self-sufficient even with no `front/.env` (e.g. CI). Step 3/Step 7 rely on this.
  - **Two `.gitignore` files exist**: root `../.gitignore` (git; `front/`-prefixed)
    and `front/.gitignore` (read by eslint's `includeIgnoreFile`, so eslint skips
    transient output). Playwright artifacts (`playwright-report/`, `test-results/`,
    `e2e/.auth/`) were added to **both**.
  - Used `browserName: "chromium"` (the bundled browser), **not**
    `devices['Desktop Chrome']` — the latter sets `channel: 'chrome'` and would
    require system Chrome.
  - `hooks.server.ts` makes **no backend call** on `/login` (only reads the auth
    cookie), so the smoke test asserts the login form directly — Step 1's "defer if
    hooks hit the backend" contingency did not apply.
  - **The Sign-In button's accessible name is the slug `"sign-in"`**, not "Sign In":
    the shared `Button.svelte` runs its `text` through `formatHandle()` for the
    `aria-label`. Role-name queries must use `/sign-?in/i` (Step 4 + §9 updated).

### Step 2 — Add testability hooks to the app

- [x] **Status:** ✅ done — 2026-06-07 — board-ready hooks (`data-testid="game-board"` + `data-scene-ready`) on `.scene-container`, `data-testid="game-board-canvas"` on `<canvas>`, `role="alert"` on the login error; gate green, 0 new svelte-check errors — commit `52d6f70`
- **Depends on:** Step 1
- **Goal:** deterministic, non-brittle hooks for the flows (these double as the
  autonomous-mode probe + a small a11y win). See §5.4.
- **Do:**
  - `BabylonEditorScene.svelte`: when scene init succeeds, set
    `data-testid="game-board"` + `data-scene-ready="true"` on the scene
    container; add `data-testid="game-board-canvas"` to the `<canvas>`.
  - `login/+page.svelte`: wire `<label for>` to the username/password inputs;
    add `role="alert"` to the error element.
- **Acceptance:** frontend gate green; **no new** `svelte-check` errors; the new
  attributes are present in the markup.
- **Verify:**
  ```bash
  cd front && npm run lint && npm run test && npm run deps:check && npm run build && npm run check
  ```
- **Notes for next agent:**
  - **The board-ready hook is on `.scene-container`** (inside
    `BabylonEditorScene.svelte`), **not** `.scene-wrapper` — that's the game
    page's outer `<div>` ([`game/+page.svelte:237`](../../../front/src/routes/game/+page.svelte)).
    Steps 4/5 selector: `[data-testid="game-board"][data-scene-ready="true"]`.
    `data-scene-ready` is a `$derived` = `!loading && error === null`, rendered as
    the string `"true"`/`"false"`; it is `"true"` **only on successful init**
    (render loop running) and stays `"false"` on scene error — so the selector is
    a true success signal, not just "loading finished".
  - **`<label for>` was already wired** on both login inputs, so
    `getByLabel('Username'|'Password')` works (as §9 noted) — the only new login
    edit was `role="alert"` on `.error-message` (Step 4's optional negative test
    can now assert it via `getByRole('alert')`).
  - **Did NOT normalise the Sign-In button's a11y name** (out of scope; shared
    `Button.svelte`, wide blast radius). Its accessible name is still the slug
    `"sign-in"` — Step 4 must query `getByRole('button', { name: /sign-?in/i })`
    (§9). §9's open question stands.
  - **Running the gate:** there is **no `front/.env`** (only `.env.example`).
    `npm run build` *and* `npm run check` both resolve `PUBLIC_API_URL` from
    `$env/static/public` and fail without it, so prefix the env var, e.g.
    `PUBLIC_API_URL=http://localhost:8000 npm run build`. **Build/check run fine
    sandboxed** once it's set (no `.env` read to block).
  - **svelte-check baseline = 55 errors / 20 warnings** (pre-existing debt,
    unchanged by this step). Use this number to confirm "no new errors" downstream.

### Step 3 — API seeding (global-setup) + wire backend into webServer

- [x] **Status:** ✅ done — 2026-06-07 — backend webServer + globalSetup wired; two players seeded via REST API with 22-card valid decks; storageState files written; smoke test still passes — commit 68bbc19
- **Depends on:** Step 1
- **Goal:** provision two players, each with a valid 22-card deck, via the public
  API; persist a logged-in `storageState` per player. See §5.2–§5.3.
- **Do:**
  - In `playwright.config.ts`: add the **backend** `webServer` entry (uvicorn
    `:8000`) and `globalSetup: './e2e/global-setup.ts'`; comment the local prereq.
  - `front/e2e/global-setup.ts`: poll a light backend endpoint (e.g. `/docs` or
    `/metrics`) until reachable; then for roles `host` and `guest`: register a
    unique user (`e2e_<role>_<runId>`), get a token, `POST /decks`, add cards
    `1..22`, assert `is_valid_for_playing`. Write creds+`deck_id` to
    `e2e/.auth/seed.json` and a Playwright `storageState` to `e2e/.auth/<role>.json`.
  - **Note (from Step 1):** the frontend `webServer` already pins `PUBLIC_API_URL`
    at build time via `webServer.env`. `global-setup.ts` runs in **Node**, so read
    the backend base URL from `process.env.PUBLIC_API_URL ?? 'http://localhost:8000'`
    (not `$env/static/public`, which is frontend-only). `e2e/.auth/` is already
    git-ignored (root + `front/.gitignore`).
- **Acceptance:** with the backend up, `npm run test:e2e` runs global-setup to
  completion and writes `e2e/.auth/host.json` + `guest.json`; Step 1's test still
  passes.
- **Verify:** (`make up` + migrations first)
  ```bash
  cd front && npm run test:e2e && ls e2e/.auth/host.json e2e/.auth/guest.json
  ```
- **Notes for next agent:**
  - **`package.json` uses `"type": "module"`** — `__dirname` is unavailable in
    ESM; `global-setup.ts` uses `fileURLToPath(import.meta.url)` instead.
  - **Card ID 12 is absent from the migration** (`001_initial_schema_and_data.py`
    seeds IDs 1–11 and 13–30, skipping 12). `CARD_IDS` in `global-setup.ts` uses
    IDs 1–11 + 13–23 (22 cards, skipping 12). Step 4's deck-present assertion
    should query the seeded deck_id from `e2e/.auth/seed.json`, not assume a
    specific set of card IDs.
  - **`storageState` format:** sets `localStorage["auth_token"]` +
    `localStorage["auth_user"]` (JSON string of the `/auth/me` response) on
    origin `http://localhost:4173`, plus an `auth_token` cookie — matching
    `front/src/lib/stores/auth.svelte.ts`.
  - **Backend `webServer` command** runs from `front/` dir:
    `cd ../back && uv run python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`.
    `reuseExistingServer: !process.env.CI` so a locally running backend is reused.

### Step 4 — Auth smoke flow (`@gating`)

- [ ] **Status:** not started
- **Depends on:** Steps 2, 3
- **Goal:** real UI login → home → lobby shows the seeded valid deck. See §5.5 A.
- **Do:** `front/e2e/auth.e2e.ts` (tag `@gating`): unauthenticated `/` redirects
  to `/login`; fill the seeded `host` creds via `getByLabel`; sign in via
  `getByRole('button', { name: /sign-?in/i })` (the button's accessible name is
  the slug `"sign-in"`, not "Sign In" — see §9); assert `/`; `goto('/game')`;
  assert the **Game Lobby** heading + the seeded deck present and selectable.
  Optional negative: bad creds → `role="alert"` error. Retire Step 1's trivial
  test (or fold it in).
- **Acceptance:** `npm run test:e2e:gating` is green (full stack up).
- **Verify:** `cd front && npm run test:e2e:gating`

### Step 5 — Game start + board render flow (`@nongating`)

- [ ] **Status:** not started
- **Depends on:** Steps 2, 3, 4
- **Goal:** two browsers create/join a room; both reach the in-game view and the
  board reports ready. See §5.5 B.
- **Do:** `front/e2e/game.e2e.ts` (tag `@nongating`): two contexts from the
  seeded `storageState` (`host`, `guest`); host selects deck → **Create New Room
  & Play**; guest selects deck → **Join Existing Room** → refresh → pick the
  joinable room → **Join Room & Play** (fallback: `room_id` handoff per §5.5);
  both assert the **Playing** view +
  `[data-testid="game-board"][data-scene-ready="true"]` visible + canvas
  non-zero size.
- **Acceptance:** `npm run test:e2e -- --grep @nongating` is green locally.
- **Verify:** `cd front && npm run test:e2e -- --grep @nongating`

### Step 6 — 3D screenshot baseline (non-gating, masked)

- [ ] **Status:** not started
- **Depends on:** Step 5
- **Goal:** a tolerant, masked visual baseline of the canvas. See §5.5 (5), §5.7.
- **Do:** in `game.e2e.ts`, add
  `await expect(canvas).toHaveScreenshot('board.png', { maxDiffPixelRatio: <t>, mask: [<dynamic>] })`;
  generate the baseline with `npm run test:e2e:update-snapshots`; commit it under
  `front/e2e/`.
- **Acceptance:** baseline committed; a second `--grep @nongating` run matches.
- **Verify:**
  ```bash
  cd front && npm run test:e2e:update-snapshots && npm run test:e2e -- --grep @nongating
  ```

### Step 7 — CI job + split gating

- [ ] **Status:** not started
- **Depends on:** Steps 4, 5, 6
- **Goal:** run the harness in CI — auth gates, 3D is non-gating. See §5.7.
- **Do:** add an `e2e` job to `.github/workflows/ci.yml` (postgres:14 + redis:7
  services; uv + Python 3.12 + `uv sync`; node 22 + `npm ci`; `alembic upgrade
  head`; `npm run build`; `npx playwright install --with-deps chromium`; start
  backend; step A `npm run test:e2e:gating` **blocking**; step B
  `npm run test:e2e -- --grep @nongating` with `continue-on-error: true`; upload
  `playwright-report/` + traces always). Add `e2e` to `ci-ok`'s `needs`.
- **Acceptance:** the `e2e` job is green on a PR; flipping one auth assertion
  fails the job + `ci-ok` (prove it, then revert); a forced 3D failure does not.
- **Verify:** open a PR; observe the `e2e` job and `ci-ok`.

### Step 8 — Docs/harness updates; complete the plan

- [ ] **Status:** not started
- **Depends on:** Step 7
- **Goal:** register the new sensor and make `front/AGENTS.md:136` executable in
  the docs; close out the effort.
- **Do:** add a running-app sensor row to [`harness.md`](../../harness.md) (and
  update the Maturity / follow-up-rungs note to reflect the gap closing); in
  [`front/AGENTS.md`](../../../front/AGENTS.md) link line 136 to this harness and
  add the `test:e2e*` scripts to the command table + Definition of Done; update
  the gate table in root [`AGENTS.md §4`](../../../AGENTS.md). **Final action:**
  move this file to [`../completed/`](../completed/).
- **Acceptance:** docs link-check passes; gates green; file moved.
- **Verify:** `lychee --offline` over the changed docs (or rely on `docs.yml`).

---

## 7. Verification (definition of done)

- Locally (after `make up` + migrations): `cd front && npm run test:e2e:gating`
  is green; `npm run test:e2e` runs both flows and produces/compares the 3D
  baseline.
- CI: the `e2e` job is green; **prove the back-pressure** by flipping one auth
  assertion and confirming the gating step fails the job + `ci-ok`; confirm a
  forced 3D failure does **not** block.
- [`front/AGENTS.md:136`](../../../front/AGENTS.md) now points at a real
  mechanism, and a new running-app sensor row exists in
  [`harness.md`](../../harness.md).

---

## 8. Risks & mitigations

| Risk | Mitigation |
| ---- | ---------- |
| WebGL/Babylon unstable headless | swiftshader flags; Flow B non-gating; `retries` + `trace`/video artifacts |
| Two-browser room-discovery timing | UI room-list path with a `room_id`-handoff fallback; **WS sparring-bot architecture stays documented as the escape hatch** |
| Screenshot nondeterminism | mask dynamic regions, pixel tolerance, non-gating, env-pinned baselines |
| Seeding slow/brittle | API seeding once in global-setup; unique users; backend seed script as later optimization |
| `PUBLIC_API_URL` build-time vs runtime inlining | ✅ resolved (Step 1): build-time (`$env/static/public`); harness sets it via `webServer.env` (§5.2) |
| Vitest/Playwright spec collision | `*.e2e.ts` naming + `testDir` + Vitest `exclude` |
| Flake blocking the repo | split gating (D3); only the cheap auth flow can block |

---

## 9. Open questions

- Exact masked regions + tolerance for the 3D screenshot (tune empirically).
- Login inputs expose proper `<label for>`, so `getByLabel('Username'|'Password')`
  works today. **But the Sign-In button's accessible name is the slug `"sign-in"`**
  — the shared `Button.svelte` runs its `text` through `formatHandle()` for the
  `aria-label` — so query it as `getByRole('button', { name: /sign-?in/i })`. Step 2
  may normalise this if the team wants the a11y name to read "Sign In" (note: it's a
  shared component used by many buttons, so weigh the blast radius).
- Whether the in-game "Playing" view is enough of a "started" signal, or we also
  assert a game-state artifact (e.g. a populated hand) for a stronger check.

## 10. Follow-up rungs (post-v1)

- **Promote Flow B (game + 3D) to gating** once stable — the next ratchet step.
- Cross-browser (WebKit) and a mobile viewport.
- Deeper gameplay flows (play a card, end a turn, resolve an attack).
- A backend **`make seed-e2e`** script if global-setup seeding gets slow.
- Wire this harness in as the **running-app verifier for autonomous mode**
  (the `creature:scene-ready` signal becomes the agent's "is it alive?" probe).
