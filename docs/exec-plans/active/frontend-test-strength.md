# Close the frontend asymmetry: enforce coverage, deepen client-logic tests

The backend engine has a four-layer ratchet — per-package coverage floors,
mutation scoring, property tests, and import-boundary contracts. The **frontend
has almost none of it**, and that asymmetry is now the largest remaining hole in
"will the overnight agent produce correct code": a change to client logic has far
less back-pressure than a change to the engine.

Three gaps, in leverage order:

0. **The frontend coverage gate is inert.** `vitest.config.ts` declares glob-keyed
   coverage floors for `ActionBuilder.ts` / `GameStateStore.ts`, but the gate runs
   `vitest run` **without `--coverage`** (`package.json → "test"`), so the
   thresholds never fire. Even the two "protected" files are unprotected in CI.
   (Tier 0 — the gate must run before anything below matters.)
1. **Only ~4 unit-test files cover ~80 `src/lib` + client-logic modules.** The
   rules-carrying client code (event reducers, model mapping, action wiring) is
   largely untested; nothing floors it. (Tier 1.)
2. **Two type/dead-code sensors are non-blocking.** `npm run check` (svelte-check,
   ~55 errors) and `npm run knip` run advisory only, so new type debt and dead
   exports slip in silently. (Tier 2.)

This plan closes them in leverage order, mirroring `harness-enforce-and-deepen.md`.
Everything here is **ralph-executable** — no human switches are required (the
frontend gate is in-repo config, unlike the backend's branch-protection/secret
switches).

## Current live state (verified 2026-07-04)

- **Frontend gate:** `npm run lint && npm run check:e2e && npm run test &&
  npm run deps:check && npm run build`. `"test"` = `vitest run --reporter=dot`
  — **no `--coverage`**, so `vitest.config.ts`'s `thresholds` block is dead code.
- **Coverage config:** `include: ["src/lib/**",
  "src/babylon-editor/src/scripts/state/**"]`; excludes the generated client,
  `**/*.svelte`, `**/*.d.ts`. Only `ActionBuilder.ts` + `GameStateStore.ts` have
  floor entries.
- **Existing unit tests (4):** `src/lib/utils/formatHandle.test.ts`,
  `src/lib/utils/getStrenghtsAndWeaknesses.test.ts`,
  `state/GameStateStore.test.ts`, `state/ActionBuilder.test.ts`.
- **Untested rules-carrying client logic:** `state/events.ts` (event reducers),
  `game/models.ts`, `game/CardDefinitionCache.ts`, `game/GameConnection.ts`,
  `src/lib/actions/*`, `src/lib/stores/**`, and 5 of 7 `src/lib/utils/*`.
- **Non-blocking sensors:** `npm run check` (svelte-check, ~55 errors) and
  `npm run knip` — both advisory (see `docs/harness.md` follow-up rungs).
- **No frontend mutation testing** (no Stryker); out of scope here (see Notes).

## How to execute

Drive one step per iteration with **`ralph-iteration`**
(`/ralph-iteration frontend-test-strength`). Pick the highest-leverage unblocked
step, implement only it, leave the **frontend gate** green
(`cd front && npm run lint && npm run check:e2e && npm run test &&
npm run deps:check && npm run build`), tick the box, stack a branch + PR, stop.
**Anti-tamper applies:** never lower a coverage floor, delete an assertion, or
exclude a file to make the gate pass — write the test or stop and report.

**`front/vitest.config.ts` is a protected path** (see `harness-guard.yml` /
`docs/harness.md`), so any step that edits it (Steps 0, and the threshold bumps in
1.x) has a **red `harness-guard` until a human applies the `harness-change`
label** — that red is the intended tripwire; note it in the PR body. Steps that
add only test files need **no** label.

## Steps

### Step 0 — Make the coverage gate actually run (Tier 0)
- [ ] **Status:** not started
- **Why / failure mode closed:** the thresholds already exist but never execute —
  the gate green-lights code that has dropped below the declared floor. Until
  coverage runs in the gate, every step below is unenforced.
- **Do:**
  - Add a `"test:coverage": "vitest run --coverage --reporter=dot"` script (or add
    `--coverage` to `"test"`) in `front/package.json`, and wire the coverage
    variant into the **frontend gate** used by CI (`.github/workflows/ci.yml`
    frontend job) and in `front/AGENTS.md` / `docs/harness.md`'s gate definition,
    so the glob thresholds fail the build on regression.
  - Confirm the two existing floors (`ActionBuilder.ts`, `GameStateStore.ts`)
    pass at their current numbers; do **not** lower them.
  - Keep `--reporter=dot`; keep the run fast (coverage on the already-tested set is
    cheap).
- **Gate:** `cd front && npm run test:coverage` fails if a floored file regresses;
  full frontend gate green. Edits `front/package.json` (unprotected) and
  `vitest.config.ts` / `ci.yml` (protected → `harness-change` label).
- **Depends on:** none. **Blocks:** every Step 1.x floor.

### Step 1a — Unit-test + floor the event reducers (`state/events.ts`) (Tier 1)
- [ ] **Status:** not started
- **Why / failure mode closed:** `events.ts` applies server events to the local
  `GameStateStore` — the client's rules mirror. A wrong reducer desyncs the board
  from the backend and passes every current gate (e2e drives *actions*, not each
  reducer branch). Highest-value untested logic; sits beside the two files already
  floored.
- **Do:**
  - Add `state/events.test.ts`: for each event type, assert the store transition
    (zone moves, health/counter deltas, turn/phase changes) with equality asserts
    on the resulting state — mirror `GameStateStore.test.ts`.
  - Add a `state/events.ts` entry to `vitest.config.ts` `thresholds`, set just
    below measured after the tests land.
- **Gate:** `cd front && npm run test:coverage` green at the new floor; full gate
  green. Test file unprotected; the threshold entry edits `vitest.config.ts`
  (protected → `harness-change` label).
- **Depends on:** Step 0.

### Step 1b — Unit-test + floor client model/mapping logic (`game/`) (Tier 1)
- [ ] **Status:** not started
- **Why / failure mode closed:** `game/models.ts` + `game/CardDefinitionCache.ts`
  translate the wire payloads into the client model; a mapping bug corrupts every
  downstream render and is invisible to the deterministic gates.
- **Do:**
  - Extend the vitest `coverage.include` to cover the pure logic under
    `src/babylon-editor/src/scripts/game/**` (keep `GameConnection.ts` out if it
    needs a live socket — test it in an `integration`-style harness or leave to
    e2e; scope this step to the pure mappers).
  - Add `game/models.test.ts` / `game/CardDefinitionCache.test.ts` with
    equality asserts on the mapped output; add floor entries.
- **Gate:** `npm run test:coverage` green at the new floors; full gate green.
  `vitest.config.ts` edit → `harness-change` label.
- **Depends on:** Step 0.

### Step 1c — Unit-test + floor `src/lib/utils` + `src/lib/actions` (Tier 1)
- [ ] **Status:** not started
- **Why / failure mode closed:** 5 of 7 `utils` and the `actions` helpers are
  untested pure functions — cheap to floor, and the exact class of "small helper
  quietly wrong" an overnight agent introduces.
- **Do:**
  - Add unit tests for the untested pure functions under `src/lib/utils/*` and
    `src/lib/actions/*`; add per-file floor entries (or a `src/lib/utils/**`
    glob floor once broadly covered).
  - Skip anything that requires the DOM/SvelteKit runtime — that belongs to e2e.
- **Gate:** `npm run test:coverage` green; full gate green. `vitest.config.ts`
  edit → `harness-change` label.
- **Depends on:** Step 0.

### Step 2 — Clear the svelte-check backlog, promote `npm run check` to gating (Tier 2)
- [ ] **Status:** not started
- **Why / failure mode closed:** ~55 svelte-check type errors run advisory, so new
  type errors hide in the noise. Clearing them and promoting the check to gating
  gives the frontend the type back-pressure the engine has from mypy-strict.
- **Do:**
  - Fix the svelte-check errors (`cd front && npm run check`) in one or more PRs —
    prioritise `babylon-editor/src` and active routes (per `docs/harness.md`).
  - Once clean, add `npm run check` to the CI frontend gate and to the gate
    definition in `AGENTS.md` / `docs/harness.md`; flip its harness-doc status
    from "non-blocking" to "gating".
- **Gate:** `cd front && npm run check` exits clean; full frontend gate green with
  `check` included. Edits `ci.yml` (protected → `harness-change` label).
- **Depends on:** none (independent of Step 0/1; large — may span several PRs).

### Step 3 — Triage knip, promote `npm run knip` to gating (Tier 2)
- [ ] **Status:** not started
- **Why / failure mode closed:** knip surfaces genuinely dead files/exports but
  runs advisory; dead code accumulates and misleads the next agent. Mirrors the
  backend `vulture + deptry` gate.
- **Do:**
  - Triage `cd front && npm run knip`: delete real dead code; add justified
    ignores for false positives in the knip config.
  - Once clean, promote `npm run knip` to the CI frontend gate; update its
    harness-doc status.
- **Gate:** `npm run knip` clean; full gate green with knip included. `ci.yml`
  edit → `harness-change` label.
- **Depends on:** none.

### Step 4 — Record the deepened frontend harness in `docs/harness.md` (close the loop)
- [ ] **Status:** not started
- **Why / failure mode closed:** the harness is owned like code — once the
  frontend coverage gate is live and the sensors are promoted, the doc must say
  so or the next agent re-discovers the gap.
- **Do:**
  - Update `docs/harness.md`: the frontend now runs a coverage gate
    (`vitest --coverage` with glob floors), lists the floored modules, and marks
    `npm run check` / `npm run knip` gating once Steps 2–3 land. Update the
    frontend gate definition in `AGENTS.md` / `front/AGENTS.md` to include the
    coverage run.
- **Gate:** docs-only → driver skips the gate; markdown link-check stays green.
  **No** label.
- **Depends on:** Steps 0–3 (so the doc states facts, not intentions).

## Notes / decisions

- **Ordering rationale.** Step 0 first — it makes every floor real; without it the
  Tier-1 floors are decoration. Tier 1 is the real coverage effort on the
  rules-carrying client logic (highest bug-catch per token). Tier 2 promotes the
  two existing advisory sensors once their backlogs clear. Step 4 records it.
- **Deliberately out of scope.** (1) **Expanding e2e** — most expensive per bug,
  Chromium-only, proves wiring not rules (same call as the backend plan). (2)
  **Frontend mutation testing (Stryker)** — high value in principle but heavy to
  stand up and slow in CI; revisit as its own plan once unit coverage exists to
  mutate against. (3) **Component (`.svelte`) coverage** — excluded from the
  vitest coverage set for now; assert UI through e2e / the future HUD→DOM
  migration instead.
- **Anti-tamper.** Floors ratchet **up** only. A step that finds a floor can't be
  met honestly must add the missing test or report — never lower the number or
  exclude the file.
