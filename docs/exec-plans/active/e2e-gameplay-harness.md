# Gameplay E2E harness — deterministic setup + driveable game state

Sequel to [`../completed/e2e-verification-harness.md`](../completed/e2e-verification-harness.md),
which got Playwright to **game start** (login → lobby → two-browser room → the
3D board renders, `[data-scene-ready="true"]`). This plan takes the running-app
sensor **past** that line — into actual gameplay (play a card, pass a phase,
swap, attack) — without trying to read pixels out of the BabylonJS canvas.

## 1. Goal & why this exists

The Playwright suite stops at `assertBoardReady()`: it proves the scene boots,
not that the game *plays*. The follow-up rung in
[`harness.md`](../harness.md) (lines ~167–168) names exactly this gap —
"deeper gameplay flows (play a card, end a turn, resolve an attack)" and "wire
the E2E harness in as the running-app verifier for autonomous mode."

The reframe that makes this tractable:

- **The rules are already tested** where they live — `app.game` is pure,
  deterministic, with pytest unit + syrupy behaviour goldens. We do **not**
  re-verify rules through a browser.
- **The e2e job is the wiring**: does an intent in the running app build the
  right action, round-trip the WebSocket, apply the server snapshot to the
  client cache, fire the right events, and reach the renderer? That glue is
  invisible to unit tests, and it has clean seams that don't involve the canvas.

Two enablers unlock it:

1. **Deterministic setup** — seed the engine RNG so the opening hand, first
   player, and dice are reproducible. Without this, *no* gameplay assertion is
   stable, however we click.
2. **A driveable, observable client** — a build-gated `window.__creature` test
   API that reads `GameStateStore` and drives actions through the **real**
   `ActionBuilder → GameConnection.sendAction` path.

## 2. Scope

### In scope (v1)
- Seed the backend game RNG via an **injected** per-game `random.Random`
  (preserving `app.game` purity); surface the seed through `Settings`.
- A build-time-gated `window.__creature` test API: read state, drive actions
  through the production code path, await state transitions deterministically.
- First gameplay specs (`@nongating`): play_card → SUPPORTING; pass phase; swap;
  attack. Assert on the client store, on the **opponent's** snapshot too.
- One **real-pointer** fidelity smoke (project a mesh → `page.mouse.click`) to
  cover the `scene.pick → InteractionManager` chain the test API skips.

### Non-goals (v1)
- **Moving the BabylonJS GUI HUD (action buttons, phase indicator, attack
  picker, turn banner) to Svelte/DOM.** That is a *separate future exec-plan*.
  Some chrome (elements indicator, card details) is already migrated; the rest
  follows later. Until then, HUD buttons are in-canvas and we drive their
  *actions* via the test API rather than clicking DOM. This plan does **not**
  depend on that migration and must not block on it.
- Re-testing game rules through the browser (covered by the engine's own tests).
- Promoting any gameplay spec to `@gating` (a later ratchet, once stable).
- Extending visual-regression screenshots to post-action states (a follow-up).

## 3. Decisions (locked) & rationale

| Decision | Choice | Why |
| --- | --- | --- |
| Determinism mechanism | **Seed the RNG** (user's call) — *not* a scenario/fixture endpoint | Smallest change; reproduces the *real* deal/turn-order pipeline rather than bypassing it. |
| Where the seed lives | Injected **per-game** `random.Random` on `GameState`, from `GameConfiguration.seed` | Keeps `app.game` pure (import-linter contract #1): engine never reads settings/global RNG. Per-game instance = no cross-room interference (vs. seeding global `random`). |
| Seed source | `Settings.game_seed` → `game_runner` builds the config | `app.websocket` may read settings; `app.game` may not. Default `None` = today's non-deterministic prod behaviour, untouched. |
| Client drive seam | `window.__creature` calling **`ActionBuilder.execute`** (the real path) | Testing a side-channel would test a fake. Same send the UI uses; server still authoritative + per-player authenticated. |
| Hook gating | **Build-time** flag (`PUBLIC_E2E_HOOKS`), tree-shaken from real prod | Avoids shipping a drive-API surface to production; mirrors the existing build-time `PUBLIC_API_URL` inlining. |
| Spec gating | `@nongating` for all gameplay specs initially | Follows the repo ratchet: flaky WebGL/WS flows settle before they block merges. |

## 4. What the app currently gives us (constraints baked into the design)

**Backend — RNG is unseeded at four sites (all module-level `random`):**
- `back/app/models/game/player.py:59` — `random.shuffle(... DECK ...)` (via
  `shuffle_deck()` at `:57`, called from `engine.create_game` at
  `back/app/game/engine.py:67`).
- `back/app/game/engine.py:73` — `first_player_id = random.choice(player_ids)`.
- `back/app/game/effects.py:478` — `random.randint(1, faces)`.
- `back/app/game/actions/combat.py:343` — `random.randint(1, faces)`.

Injection points:
- `GameConfiguration` — `back/app/models/game/state.py:57` (has `initial_draw`).
- `GameState` / `GameState.create(room, config)` —
  `back/app/models/game/state.py:69` / `:100`.
- Engine entry — `create_game` (`engine.py:63`), `start_game` (`engine.py:71`).
- Settings-aware caller — `back/app/websocket/game_runner.py:46` (`create_game`)
  / `:49` (`start_game`); kicked off from `session.py:62`.
- `Settings` — `back/app/settings/config.py:6`.

**Frontend — a clean, DOM-free state/event layer already exists:**
- `GameStateStore` (singleton, no Babylon imports) — getters `state`,
  `myPlayerId`, `validActions`, `isMyTurn`, `currentPhase`
  (`front/src/babylon-editor/src/scripts/state/GameStateStore.ts:42–58`);
  `applyServerState()` is the snapshot entry point.
- `BoardController.instance` (`.../BoardController.ts:28`) — typed event bus
  `.on(...)` emitting `gameStarted`, `stateReplaced`, `cardMoved`,
  `cardsSwapped`, `phaseChanged`, `turnChanged`, `attackDeclared`,
  `cardHealthChanged`, `cardDestroyed`, `gameOver`, … ; `applyServerState`
  called at `:113`.
- `GameConnection.instance` → `getStateStore()`; **single send point**
  `sendAction(actionData)`. `ActionBuilder.execute(validAction)` wraps it.
- `InteractionManager` resolves a picked mesh → `CardEntity` → chooses a
  `ValidAction` → `ActionBuilder.execute`. Card meshes are named
  `Card_<instanceId>`; `CardEntityManager` maps mesh ↔ entity. Zone anchors are
  named (`My_Supporting_Anchor`, …).
- Bootstrap order (App.ts / scene init): GameConnection → BoardController →
  AnimationManager + InteractionManager + HudController. Scene-ready surfaces as
  `data-scene-ready` on `.scene-container`
  (`front/src/lib/components/BabylonEditorScene.svelte:53`, `:162`).
- **No `window`-exposed hook exists today** — the test API is net-new.
- The **HUD is drawn in-canvas** (Babylon GUI `AdvancedDynamicTexture`), so its
  buttons are not DOM-clickable. v1 drives their actions via the test API.

## 5. Design

### 5.1 Coverage map (what each layer proves — and doesn't)

| Layer | Proves | Does **not** prove |
| --- | --- | --- |
| Engine tests (exist) | Game rules / state transitions | Any wiring outside the engine |
| **`window.__creature` (primary)** | intent → action build → WS → server → snapshot → store → event bus, both clients | mouse→pick→InteractionManager selection; that the mesh visually moved |
| **Real-pointer smoke (secondary)** | `scene.pick` + InteractionManager two-step selection with real input | full per-action coverage (that's the API layer's job) |
| Screenshot baseline (exists; extend later) | the picture renders | logic/state correctness |

### 5.2 Backend: inject a per-game seeded RNG (purity-preserving)

- Add `seed: int | None = None` to `GameConfiguration`.
- Add a **non-serialized** per-game `rng: random.Random` to `GameState` (Pydantic
  `PrivateAttr` or `Field(exclude=True)` with `arbitrary_types_allowed`) so it
  never leaks into `serialize_for_player`. Initialise in `GameState.create`:
  `rng = random.Random(config.seed)` (`None` → system entropy = today's
  behaviour).
- Replace the four module-level `random.*` calls with the per-game instance:
  - `shuffle_deck()` takes an `rng` param; engine passes `state.rng` at
    `engine.py:67`.
  - `engine.py:73` → `state.rng.choice(player_ids)`.
  - `effects.py:478` / `combat.py:343` → `state.rng.randint(...)` (state is in
    scope in both).
- **State lifetime — confirmed in-memory per room** (see §9): `game_runner`
  stores the live object on `room.state` and reads it back from the in-process
  `Lobby.rooms` dict; Redis holds only membership sets, never game state. So a
  live `random.Random` on `GameState` persists across actions ⇒ full-session
  determinism (incl. mid-game dice) from a single seed at `create_game` — **no
  `getstate()`/`setstate()` plumbing needed.** The one assumption to lock down:
  the engine pipeline must **mutate state in place** (it does — the reducer
  mutates) rather than rehydrate from a dict, which would drop a `PrivateAttr`.
  Step 1 guards this with a multi-action determinism test, not a contingency.

### 5.3 Backend: surface the seed through settings

- `Settings.game_seed: int | None = None` (`config.py`), read as its env var
  (`GAME_SEED`, per the `model_config` env mapping).
- `game_runner` builds `GameConfiguration(seed=settings.game_seed)` for the
  engine it uses for `create_game`/`start_game`. Prod default `None` =
  unchanged. `app.websocket` importing settings respects the layered contract.

### 5.4 Frontend: `window.__creature` test API (build-gated)

New module `front/src/babylon-editor/src/scripts/devtools/E2EHarness.ts`
(beside the existing `DevToolPanel.ts`; `.dependency-cruiser.cjs` excludes
`src/babylon-editor`, so the `src/lib` layering rules don't constrain it).
Attached from the scene bootstrap **after `BoardController.instance` is set**,
only when hooks are enabled.

**Flag plumbing (resolved in Step 4 — `$env/static/public` does NOT work here):**
the original plan was to read `PUBLIC_E2E_HOOKS` via `$env/static/public`, but
that has no working form: a **named** import breaks `npm run build` when the var
is unset (SvelteKit only `export const`s vars that are set, so the import is a
hard Rollup error); a **namespace** import (`import * as`) avoids the error but is
not a compile-time constant, so it never tree-shakes; and a **dynamic** `import()`
in a dead branch still leaves an orphan chunk. The working mechanism is a vite
`define`: `vite.config.ts` inlines `__CREATURE_E2E_HOOKS__` as a literal boolean
(`process.env.PUBLIC_E2E_HOOKS === "1"`, read at build), and
`BabylonEditorScene.svelte` does a **static** `import { attachE2EHarness }` whose
only call site is `if (__CREATURE_E2E_HOOKS__) { attachE2EHarness(); }` in
`initScene` (after `BoardController.instance` is set). When the constant is
`false`, the side-effect-free module is fully eliminated — **no chunk emitted**.
`PUBLIC_E2E_HOOKS=1` is still the env flag (set in the e2e build `webServer.env`);
only the read mechanism changed. Thin facade over the existing singletons:

- **Read:** `getState()`, `validActions()`, `phase()`, `isMyTurn()`,
  `cardsInZone(zone, perspective)` — straight off `GameStateStore`.
- **Drive (real path):** `dispatch(validAction)` plus ergonomic helpers
  `playCard(instanceId)`, `pass()`, `swap(a,b)`, `attack(attackerId, targetId?)`,
  `promote(...)` — each looks up the matching entry in `store.validActions` and
  runs it through `ActionBuilder.execute → GameConnection.sendAction`. Never a
  side channel.
- **Wait (no sleeps):** `waitForState(predicate, timeout)` and
  `nextEvent(name, timeout)` resolve off `BoardController.instance.on(...)`
  (`stateReplaced` / granular events). Specs await these, not timers.

Gating: `PUBLIC_E2E_HOOKS` is unset in normal builds (hook tree-shaken away) and
set only for the e2e preview build (§5.6). The drive API is no privilege
escalation — the WS is per-player authenticated and the server validates every
action — but build-gating keeps the surface out of real prod entirely.

### 5.5 Real-pointer fidelity smoke (secondary)

Add `screenPositionOf(instanceId)` to the harness: `Vector3.Project` the mesh's
absolute position with `scene.activeCamera` + `engine.getRenderWidth/Height()`,
offset by the canvas bounding box → page coords. A spec then does
`page.mouse.click(x, y)`, exercising `scene.pick → InteractionManager` selection
→ the same `play_card` outcome as the API spec. Keep it to **one** interaction;
it's the brittle (camera/layout-dependent) layer.

### 5.6 E2E plumbing & CI

- `playwright.config.ts`: add `GAME_SEED` to the **backend** `webServer.env`
  (alongside `DATABASE_URL`/`REDIS_URL`, lines ~65–68) and `PUBLIC_E2E_HOOKS=1`
  to the **frontend** build `webServer.env` (alongside `PUBLIC_API_URL`,
  ~81–83, inlined at build time).
- Optionally expose `GAME_SEED` + the resulting known opening hand via
  `e2e/config.ts` so specs can assert against expected card ids.
- Gameplay specs stay `@nongating`; CI's existing `continue-on-error` non-gating
  step runs them. No new job needed.

## 6. Execution queue (work orders)

Each step is independently shippable and ends at a named gate, for
`/ralph-iteration`. Backend gate = `cd back && make check`; frontend gate =
`npm run lint && npm run test && npm run deps:check && npm run build`; e2e =
`npm run test:e2e` (or `-- --grep @nongating`).

### Step 1 — Backend: per-game seeded RNG (purity-preserving)
- [x] **Status:** ✅ done — 2026-06-10 — per-game `GameState.rng` (PrivateAttr) seeded from `GameConfiguration.seed`; 4 module-level `random.*` sites now use it; new `test_rng_determinism.py` — branch `spec/e2e-gameplay-harness/step-1/seeded-rng` (tip = the iteration commit) — PR blocked (see note)
- Notes for next agent:
  - **PR submission is blocked by repo remote/Graphite access** (not a code issue): `gt submit` errors with "could not verify you have access to the repo andrsabril/creature"; `gh` can't resolve that repo under the authed account `hector-soria-clio`; `origin` uses SSH host-alias `github.com-hec` with push URLs for both `andrsabril/creature` and `Hectortilla/creature`. Every step in the predecessor plan (`../completed/e2e-verification-harness.md`) likewise recorded **commits only, no PR URLs** — same barrier. I fixed a doubled-owner bug in `.git/.graphite_repo_config` (`name` was `andrsabril/creature`, now `creature`) but the access error persists. The iteration commit is the tip of branch `spec/e2e-gameplay-harness/step-1/seeded-rng` (stacked on `main`); whoever has working remote access should `gt submit --stack` / open the PR. The next iteration can still `gt checkout spec/e2e-gameplay-harness/step-1/seeded-rng` to stack on it.
  - The shared `_build_game()` in `tests/unit/test_engine_smoke.py` now seeds via `GameConfiguration(seed=1234)` (default arg) instead of `random.seed(1234)`; the behaviour goldens (`tests/behaviour/`) inherit this and **passed unchanged** — `random.Random(1234)` reproduces the same Mersenne-Twister stream in the same call order, so no golden regeneration was needed. If you change RNG *call order*, expect goldens to shift.
  - `instance_id` is a per-card uuid (non-deterministic by design); compare seeded deals by template `card_id`, as `test_rng_determinism.py` does.
  - `rng` is a `PrivateAttr` (`_rng`) with a public `state.rng` property — automatically excluded from `model_dump`/`serialize_for_player` (asserted in the new test). Step 2 can read `state.rng` directly; no plumbing needed.
- Add `seed` to `GameConfiguration`; add non-serialized `rng: random.Random` to
  `GameState`, initialised in `create()`; replace the 4 module-level `random.*`
  sites (player shuffle, first-player choice, effects/combat dice) with
  `state.rng`. Confirm `rng` is excluded from `serialize_for_player`.
- Add a unit test: same seed ⇒ identical opening hand + first player across two
  `create_game`+`start_game` runs; `None`/different seed ⇒ differs.
- **Gate:** `cd back && make check` (mypy-strict on `app.game`, ruff,
  import-linter purity intact, behaviour goldens green — regenerate goldens only
  if a deliberate, reviewed change).

### Step 2 — Backend: surface seed via `Settings` → `game_runner`
- [x] **Status:** ✅ done — 2026-06-10 — `Settings.game_seed` (env `GAME_SEED`); `GameRunner.__init__` builds `GameConfiguration(seed=settings.game_seed)` and passes it to `get_engine(...)`; new `test_rng_multi_action.py` proves dice + rng position reproduce across a multi-action sequence and the live `_rng` object is never dropped — branch `spec/e2e-gameplay-harness/step-2/settings-seed` (stacked on step-1's branch) — PR blocked (same remote-access barrier as step 1)
- Notes for next agent:
  - **PR still blocked by repo remote/Graphite access** (not a code issue) — same as step 1's note: `gt submit`/`gh` can't reach the remote under the authed account. The step-2 commit is the tip of `spec/e2e-gameplay-harness/step-2/settings-seed`, stacked on `spec/e2e-gameplay-harness/step-1/seeded-rng`. Step 3 can `gt checkout spec/e2e-gameplay-harness/step-2/settings-seed` to stack on it.
  - **Singleton caveat:** `get_engine()` is a module-level singleton (`engine.py:198`) — it honours the passed config only on the *first* call, when `_engine is None`. In prod that first call is `GameRunner.__init__` (lifespan builds exactly one runner), so the seed always takes. If a future test/caller invokes `get_engine()` before the runner is built, the seed config would be ignored — set it explicitly there if that ever matters.
  - **State-lifetime question (§9) is now confirmed by test, not just by reading:** `test_rng_multi_action.py::test_same_seed_reproduces_dice_across_actions` asserts `state.rng is rng_obj` after every `process_action` — the reducer's in-place mutation preserves the live `_rng` PrivateAttr, so single-seed determinism covers mid-game dice. **No `getstate()`/`setstate()` plumbing is needed** for Step 6's attack-dice determinism.
  - The dice in the new test come from a deck where each card carries a dice-gated `apply-status` effect (`dice_face=7`, `faces=6` ⇒ never matches, so it only emits a `DiceRolledEvent` without altering combat). Reuses the smoke suite's `_make_deck`/`_act_player_id`/`_client_payload` driver helpers.
  - For Step 3, the e2e backend just needs `GAME_SEED` in `playwright.config.ts`'s backend `webServer.env`; the plumbing all the way to the engine is done and verified (`GAME_SEED=42` → `Settings.game_seed=42` → `GameConfiguration.seed=42`).
- Add `Settings.game_seed: int | None = None` (env `GAME_SEED`, no prefix —
  §9); build `GameConfiguration(seed=settings.game_seed)` in `game_runner`
  (`self.engine`/`get_engine()`). Default `None` = unchanged prod behaviour.
- State is in-memory per room (§9), so also add a **multi-action determinism**
  test: same seed ⇒ identical dice across a sequence of actions (guards the
  in-place-mutation assumption — that a `PrivateAttr` rng isn't dropped).
- **Gate:** `cd back && make check`; manual: boot backend with `GAME_SEED=42`,
  start a game twice, confirm identical opening hand (logs/WS).

### Step 3 — E2E plumbing: pass the seed to the e2e backend
- [x] **Status:** ✅ done — 2026-06-10 — added `E2E_GAME_SEED` (env `GAME_SEED`, default `"42"`) to `e2e/config.ts`; wired it into the backend `webServer.env` in `playwright.config.ts` alongside `DATABASE_URL`/`REDIS_URL`. All 3 e2e specs pass unchanged. — branch `spec/e2e-gameplay-harness/step-3/seed-plumbing` (stacked on step-2's branch) — PR blocked (same remote-access barrier as steps 1–2)
- Notes for next agent:
  - **PR still blocked by repo remote/Graphite access** (not a code issue) — same as steps 1–2: `gt submit`/`gh` can't reach the remote under the authed account. The step-3 commit is the tip of `spec/e2e-gameplay-harness/step-3/seed-plumbing`, stacked on `spec/e2e-gameplay-harness/step-2/settings-seed`. Step 4 can `gt checkout spec/e2e-gameplay-harness/step-3/seed-plumbing` to stack on it.
  - **`E2E_GAME_SEED` is a string** (`process.env.GAME_SEED ?? "42"`) because Playwright `webServer.env` values must be strings; the backend's `Settings.game_seed: int | None` coerces it (pydantic-settings parses `"42"` → `42`). Gameplay specs (Steps 5–7) should import `E2E_GAME_SEED` from `e2e/config.ts` so the seed and the expected hand live in one place.
  - The "expected opening hand" surfacing (mentioned as optional in the step) was **deferred** — there's no known-hand constant yet. Derive it in Step 5 when the first gameplay spec needs concrete card ids to assert against; the seed (`42`) is fixed and reproducible per the Step 1 determinism test.
  - Verified: full `npm run test:e2e` green (3 passed, ~38s) with the backend booted under `GAME_SEED=42`; the prod-build frontend `webServer` is untouched (no `PUBLIC_E2E_HOOKS` yet — that's Step 4). Run needs Postgres+Redis up (`make up`) and the sandbox off.

### Step 4 — Frontend: build-gated `window.__creature` API
- [x] **Status:** ✅ done — 2026-06-10 — added `devtools/E2EHarness.ts` (read off `GameStateStore` + drive via `ActionBuilder.execute` + `waitForState`/`nextEvent` off the `BoardController` event bus); `attachE2EHarness()` is called from `BabylonEditorScene.svelte`'s `initScene` (after `BoardController.instance` is set), guarded by a vite `define` build constant `__CREATURE_E2E_HOOKS__`; `PUBLIC_E2E_HOOKS=1` added to the frontend build `webServer.env`. Tree-shaking verified both ways. — branch `spec/e2e-gameplay-harness/step-4/e2e-harness-api` (stacked on step-3's branch) — PR blocked (same remote-access barrier as steps 1–3)
- Notes for next agent:
  - **PR still blocked by repo remote/Graphite access** (not a code issue) — same as steps 1–3: `gt submit`/`gh` can't reach the remote under the authed account. The step-4 commit is the tip of `spec/e2e-gameplay-harness/step-4/e2e-harness-api`, stacked on `spec/e2e-gameplay-harness/step-3/seed-plumbing`. Step 5 can `gt checkout spec/e2e-gameplay-harness/step-4/e2e-harness-api` to stack on it.
  - **Gating mechanism changed from the plan's `$env/static/public` to a vite `define` constant** (`__CREATURE_E2E_HOOKS__`). Why: a `$env/static/public` *named* import of `PUBLIC_E2E_HOOKS` **breaks `npm run build` when the var is unset** — SvelteKit's `create_static_module` only emits `export const` for vars that are actually set, so a missing named import is a hard Rollup error ("not exported by virtual:env/static/public"). A *namespace* import (`import * as`) avoids the error but is **not a compile-time constant**, so it does not tree-shake. And even a *dynamic* `import()` inside a dead `if` branch leaves an **orphan chunk** in the output. The working combination is: vite `define` inlines `__CREATURE_E2E_HOOKS__` as a literal boolean (read from `process.env.PUBLIC_E2E_HOOKS` at build) + a **static** guarded `import { attachE2EHarness }` whose only call site is the dead branch → the side-effect-free module is fully eliminated, **no chunk emitted**. §5.4 updated to match. The `webServer.env` flag is still `PUBLIC_E2E_HOOKS=1` (the define reads it), so playwright plumbing is unchanged from the plan.
  - **Verified tree-shaking:** `PUBLIC_API_URL=… npm run build` (no hooks) ⇒ `__creature`/`E2EHarness`/`attachE2EHarness` absent from `.svelte-kit/output/client/_app` (grep count 0); `PUBLIC_API_URL=… PUBLIC_E2E_HOOKS=1 npm run build` ⇒ `__creature` present. Note: `npm run build` needs `PUBLIC_API_URL` set inline (the sandbox denies reading `front/.env`).
  - **svelte-check baseline unchanged at 55 errors** (all pre-existing babylon-editor type debt); `E2EHarness.ts` adds none. The two `BabylonEditorScene.svelte` errors (lines ~71 `loadScene`, ~153 `Scene` cross-`node_modules` type mismatch) pre-date this step. `app.d.ts` declares `__CREATURE_E2E_HOOKS__` **inside `declare global`** (module-scope `declare const` is invisible to consumers — that was a real svelte-check error I had to fix).
  - **Drive API ↔ backend action names** (confirmed against `back/app/game/actions/`): `play_card` (`instance_id`), `pass`, `swap` (`supporting_card_id`/`attacking_card_id`), `attack` (`attacker_id`/`target_card_id`; pass no target for the no-defender case), `promote` (`instance_id`). Helpers look up the matching entry in `store.validActions` and `throw` if absent — so a spec that drives an action the server didn't offer fails fast with a clear message.
  - For Step 5: import `attachE2EHarness`'s window surface as `window.__creature` in the spec via `page.evaluate`. `waitForState(predicate)` re-checks after any of a curated event list and is the no-sleep primitive; `nextEvent(name)` resolves one granular event. The store is updated **before** events fire, so predicates always see fresh state. There's still **no known opening-hand constant** (deferred from Step 3) — derive it from the seeded deal when the first assertion needs concrete `card_id`s, and keep it beside `E2E_GAME_SEED` in `e2e/config.ts`.
- Add `E2EHarness.ts` (read + drive-via-`ActionBuilder` + `waitForState`/
  `nextEvent`). Gate the `window.__creature` attach behind a build constant so it
  is tree-shaken from normal/prod builds (see §5.4 for the vite-`define`
  mechanism and why `$env/static/public` does not work here). Add `PUBLIC_E2E_HOOKS`
  to the frontend build `webServer.env`.
- **Gate:** frontend gate green; **verify tree-shaking** — `__creature` absent
  from a normal `npm run build` bundle, present only with the flag; 0 new
  eslint/svelte-check errors; `deps:check` clean (module placement).

### Step 5 — First gameplay spec: play_card → SUPPORTING (`@nongating`)
- [ ] **Status:** not started
- New `e2e/gameplay.e2e.ts` reusing the host/guest contexts + `assertBoardReady`
  from `game.e2e.ts`. Via `window.__creature`: dispatch `play_card` for a known
  (seeded) hand card; `waitForState` until that `instance_id` is in SUPPORTING;
  assert on the store **and** on the guest's snapshot (multiplayer round-trip).
- **Gate:** `npm run test:e2e -- --grep @nongating` green; frontend gate green.

### Step 6 — Extend: pass phase, swap, attack (`@nongating`)
- [ ] **Status:** not started
- Specs: pass advances `currentPhase` through the expected sequence; swap
  exchanges supporting/attacking instance ids; attack drops defender health /
  destroys it (assert `cardHealthChanged`/`cardDestroyed`). Attack-dice
  determinism depends on Step 2's state-lifetime finding.
- **Gate:** `--grep @nongating` green.

### Step 7 — Secondary: real-pointer fidelity smoke (`@nongating`)
- [ ] **Status:** not started
- Add `screenPositionOf(instanceId)`; one spec projects a hand card,
  `page.mouse.click`s it, asserts the same `play_card` outcome as Step 5 —
  proving `scene.pick → InteractionManager`. Keep it to one interaction.
- **Gate:** `--grep @nongating` green.

### Step 8 — Docs/harness updates; complete the plan
- [ ] **Status:** not started
- Update `docs/harness.md`: tick "deeper gameplay flows" in the follow-up rung;
  note the seed + `window.__creature` as the autonomous-mode probe surface;
  cross-link this plan. Note the HUD→Svelte migration as a *separate* future
  plan enabling DOM-level HUD assertions. Move this file to `../completed/`.
- **Gate:** docs link-check; full frontend + backend gates.

## 7. Verification (definition of done)
- Same `GAME_SEED` ⇒ byte-identical opening hand + first player, every run
  (backend unit test + observed in e2e).
- `@nongating` gameplay specs (play_card, pass, swap, attack) pass locally and
  in CI's non-gating step; each asserts on the **client store** and at least one
  asserts the **opponent's** snapshot.
- One real-pointer spec drives a click through the canvas to the same outcome.
- `__creature` is absent from a normal production build.
- Backend purity intact (`make arch`), full gates green both halves.

## 8. Risks & mitigations
- **Pydantic + `random.Random`** (not serializable) → `PrivateAttr`/`exclude`;
  explicitly assert it's absent from `serialize_for_player` output.
- **Mid-game dice non-determinism if state is re-hydrated** → Step 2 records the
  lifetime and persists `getstate()` if needed; setup-time determinism is
  unaffected regardless.
- **Drive-API leaking to prod** → build-time flag + a Step-4 bundle check.
- **Real-pointer brittleness** (camera/layout/projection) → keep it to one
  non-gating interaction; the API layer carries breadth.
- **Behaviour goldens shift** when RNG threading changes call order → expect
  `None`-seed output to be unchanged; if goldens move, review the diff before
  regenerating (don't blindly `--snapshot-update`).

## 9. Resolved questions (answered from the code, not decisions)
- **Env var → `GAME_SEED`.** `Settings` (`config.py:6`) is `BaseSettings` with
  no `env_prefix` (`model_config = {"env_file": ".env"}`), so fields map
  case-insensitively to upper-case env vars — like `database_url`←`DATABASE_URL`.
- **`GameState` is in-memory per room.** `game_runner` stores the live object on
  `room.state` (lines 47/52/99) and reads it from the in-process `Lobby.rooms`
  dict; `room_registry` uses Redis only for membership sets, never game state.
  ⇒ a live RNG persists across actions; single-seed determinism covers dice too
  (guarded by the Step 2 test). No `getstate()` plumbing.
- **`E2EHarness.ts` → `babylon-editor/src/scripts/devtools/`.**
  `.dependency-cruiser.cjs` excludes `src/babylon-editor` from its cruise scope,
  so the `src/lib` layering rules don't apply; placing it beside the existing
  `DevToolPanel.ts` is consistent and conflict-free.

## 10. Follow-up rungs (post-v1)
- Promote stable gameplay specs `@nongating → @gating`.
- Extend the screenshot baseline to canonical post-action states (card in
  supporting zone, attacking row, post-swap), pinned to SwiftShader, non-gating.
- The **HUD→Svelte/DOM migration** (separate plan): once the action buttons /
  phase indicator / attack picker / turn banner are DOM, assert them with
  `getByRole` and drop the corresponding test-API reliance — plus the
  accessibility/i18n payoff.
- Wire `window.__creature` + the seeded deal as the autonomous-mode "is it
  playing?" probe (beyond today's `[data-scene-ready]`).
