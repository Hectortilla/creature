# Make the harness trustworthy for the unattended overnight loop

The harness is broad and deterministic (H2), but it has the wrong *shape* for an
**unsupervised** agent. A multi-perspective audit (8 dimensions, 60 gaps) found
the dominant weakness is not a coverage gap — it is that the gate the overnight
loop relies on is **self-reported and agent-editable**, and the one multi-step
engine sensor **pins zero numbers**. This plan closes those holes in leverage
order so an overnight ralph loop can almost always be trusted to produce correct
results.

## Goal & why this exists

Two failure classes let an overnight agent ship wrong code green:

1. **The gate is a self-report, not a fact.** `scripts/ralph_loop.py:649-660`
   defines `progressed` as `after_head != before_head` (a commit happened) **or**
   `after_boxes < before_boxes` (a box got ticked) — it **never runs `make verify`
   or `make check`** (grep-confirmed: the only `subprocess` uses are git ops +
   launching Claude). Whether a change is gate-green lives only in the agent's
   prose. Recent iterations self-granted "docs-only" skips
   (`.ralph/logs/20260618-145843/iter-001.log.md`, `iter-004.log.md`).
2. **The gate is editable, and the engine sensor is shallow.** Nothing stops the
   agent regenerating the syrupy golden, lowering `fail_under = 62`
   (`back/pyproject.toml:150`), `xfail`-ing a test, or widening a boundary to turn
   red green — and the one behaviour golden fingerprints **event class names
   only** (`_event_types`, `back/tests/behaviour/test_engine_behaviour.py:25-31`
   explicitly discards payloads), so wrong damage / element bonus / win condition
   ship green because the same event *types* still fire. `calculate_damage`,
   `get_element_bonus`/`get_total_element_bonus`, and `check_game_end` have **zero**
   direct tests (grep-confirmed).

The fix is two-fold and ordered: first make the gate **tamper-evident and
machine-executed** (Steps 1–3), then add an **independent number-pinning sensor**
that survives a golden regeneration (Steps 4a/4b). Steps 5–8 harden the rest.

**Decided scope (what we are NOT doing, and why):**
- **Not expanding E2E.** It's the most expensive sensor per bug, Chromium-only,
  "proves wiring not rules" by its own comment (`front/e2e/attack.e2e.ts`), and
  freely agent-editable. The only e2e change here is config (Step 3).
- **Not chasing the `fail_under` coverage %.** It measures lines-run, is gameable,
  and is orthogonal to bugs-caught. Pin *outcomes* instead (Step 4).
- **Not making services/websocket fully mypy-strict or building a full
  integration suite.** Too broad, lower leverage than two targeted invariant
  tests (Step 7).

## Background corrections (audit vs. current repo)

- `.github/CODEOWNERS` **already exists** and covers `/back/app/game/`,
  `/back/pyproject.toml`, `/.github/`, `/docs/harness.md` — Step 1 **extends** it,
  doesn't create it.
- A `ci-ok` aggregation job **already exists** (`.github/workflows/ci.yml:234-247`)
  and explicitly treats **`skipped` as OK**. Combined with the `dorny/paths-filter`
  (`ci.yml:14-31`, triggers only on `back/**` / `front/**` / `ci.yml`), a PR
  touching only root `Makefile`, `scripts/**`, `docs/**`, or `.claude/**` runs
  **zero substantive jobs yet `ci-ok` is green** — Step 5's hole.
- `scripts/ralph_loop.py` is **not** covered by ruff/pre-commit, so Step 2's gate
  is a functional dry-run, not `make check`.

## How to execute

Drive one step per iteration with the **`ralph-iteration`** skill
(`/ralph-iteration harness-overnight-trust`). Pick the highest-leverage unblocked
step, implement only it, leave **`make verify`** green, tick the box, stack a
branch + PR, stop. **Important for the loop:** Steps that touch harness-defining
paths (the golden, `pyproject.toml`, `ci.yml`, `Makefile`, `.claude/skills/`,
`vitest.config.ts`, `front/e2e/**`) will trip the Step 1 guard and show **red on
CI until a human applies the `harness-change` label** in the morning. That red is
**intended** — it is the human tripwire, not a bug. Do **not** revert a legitimate
harness change to make the guard green; record in the PR body that it needs the
label.

## Steps

### Step 1 — Make the harness tamper-evident (CI guard + CODEOWNERS + anti-tamper rule)
- [ ] **Status:** _not started_
- **Why / failure mode closed:** the agent makes a red check green by regenerating
  the `.ambr` golden, lowering `fail_under`, deleting/`xfail`-ing a test, flipping
  `continue-on-error`, or widening an import-linter contract — and the loop banks
  the commit as progress. This is the keystone: every sensor below is worthless
  until the agent cannot silently disable it. It is a **CI / merge-time** control
  (it does not block the local loop gate); its job is to make harness edits
  impossible to merge without a human's eyes.
- **Do:**
  - Add `.github/workflows/harness-guard.yml` — a job that runs on **every** PR
    (no paths-filter), diffs against the base (`git diff --name-only
    origin/${{ github.base_ref }}...HEAD`), and **hard-fails** if any changed path
    matches the protected set **and** the PR does not carry a `harness-change`
    label (read the label via `github.event.pull_request.labels` or `gh pr view`).
    Protected set: `back/tests/behaviour/__snapshots__/*.ambr`,
    `back/pyproject.toml`, `back/Makefile`, `Makefile`,
    `.github/workflows/**`, `front/vitest.config.ts`, `front/playwright.config.ts`,
    `front/e2e/**`, `scripts/ralph_loop.py`, `.claude/skills/**`,
    `.pre-commit-config.yaml`. Add `harness-guard` to `ci-ok`'s `needs`
    (`ci.yml:235`) so it's required, and document the `harness-change` label.
  - Extend `.github/CODEOWNERS` to cover the protected paths not already listed:
    `/back/tests/behaviour/__snapshots__/`, `/Makefile`, `/back/Makefile`,
    `/front/vitest.config.ts`, `/front/playwright.config.ts`, `/front/e2e/`,
    `/scripts/`, `/.claude/skills/`.
  - Add an **anti-tampering clause** to `.claude/skills/ralph-iteration/SKILL.md`
    (a new bullet in the Procedure, step 3): *"Never delete, skip, or `xfail` a
    test; never weaken an assertion; never lower a threshold (`fail_under`, vitest
    `thresholds`); never regenerate a golden/snapshot, widen an import-linter
    contract, or set `continue-on-error` in order to make the gate pass. If a gate
    is red, fix the code — or stop and report. Making the gate green by editing the
    gate is a failed iteration."*
- **Gate:** `cd back && make check` still green (this step is CI + docs only and
  does not touch app code). Lint the new YAML mentally / `actionlint` if available.
  This step's *own* PR touches protected paths, so its `harness-guard` check will
  be red until the `harness-change` label is applied — expected; note it in the PR.
- **Depends on:** none.

### Step 2 — Make the loop driver execute the gate itself (kill the self-report)
- [ ] **Status:** _not started_
- **Why / failure mode closed:** the agent commits code that was never
  gate-verified, or mislabels a real change as "docs-only" and skips `make verify`
  — and the driver counts it as progress anyway. This makes "is it green" a
  **machine fact** in the driver, independent of the agent's prose.
- **Do:**
  - In `scripts/ralph_loop.py`, after `run_iteration` returns and a commit is
    detected (`after_head != before_head`), have the **driver** run the gate via
    `subprocess.run` and treat a non-zero exit as a **hard failure** of the
    iteration: do **not** count it as `progressed`, increment `stalls`, surface the
    gate output in the iteration log, and (configurably) abort the loop. Run
    `make verify` (repo root) by default; allow a `--gate` override
    (`make check` for backend-only runs / faster local loops).
  - Restrict any docs-only fast-path to a **hard allowlist**: skip the gate only
    when *every* changed path matches `docs/**/*.md`. Anything touching `Makefile`,
    `scripts/**`, `ci.yml`, `.claude/**`, or code is **not** docs-only and must run
    the gate. Compute the changed set from `git diff --name-only
    before_head..after_head`.
  - Add `scripts/` to ruff's scope (rider) so the driver is itself linted, or note
    why not.
- **Gate:** the driver isn't covered by the test suite, so verify functionally:
  (a) a **dry-run** where the iteration makes a trivially-passing change → driver
  runs `make verify`, sees green, counts progress; (b) a dry-run where the change
  breaks a unit test → driver runs the gate, sees red, marks the iteration failed
  and does **not** count progress. Capture both in the PR body. `cd back && make
  check` green for any Python touched. Needs `make up` + sandbox off to exercise
  the real gate.
- **Depends on:** none (independent of Step 1, but pairs with it thematically).

### Step 3 — Two config fixes: drop the loop-gate retry mask + delete stale `@nongating` text
- [ ] **Status:** _not started_
- **Why / failure mode closed:** (a) `Makefile:24` forces `npm run test:e2e --
  --retries=2` in the **commit-deciding** loop gate, so a real intermittent race
  passes 1-in-3 and the loop records green — the documented flaky-retry footgun.
  (b) `.claude/skills/ralph-iteration/SKILL.md` (≈ lines 73-85) still tells the
  agent gameplay e2e is `@nongating` / "runs report-only" / "does not block",
  though the whole suite is now `@gating` and blocking (`docs/harness.md`) — so the
  skill actively *teaches* the agent to ignore a now-gating failure.
- **Do:**
  - Edit `Makefile:24`: drop the forced `-- --retries=2` from the `verify` target's
    e2e line (Playwright's config already uses `retries: CI ? 2 : 0`, so the local
    loop gate runs with 0 retries — no masking). CI keeps its own `retries: 2` for
    cross-machine noise; only the *commit-deciding* gate must not mask. Optionally
    add `--max-failures=1` for strictness.
  - In `SKILL.md`, delete/rewrite the `@nongating`/report-only lines so the skill
    states the whole e2e suite is `@gating` and blocking, and that any e2e failure
    fails the iteration (matches `docs/harness.md` end-state).
- **Gate:** `make verify` green with retries dropped (if it flakes without
  retries, that's a real flake to fix — record it; do not re-add retries to mask
  it). Touches `Makefile` + `SKILL.md` (protected → needs the `harness-change`
  label on the PR).
- **Depends on:** none.

### Step 4a — Pin engine numbers: direct unit tests for damage / element math + validator rejections
- [ ] **Status:** _not started_
- **Why / failure mode closed:** the single most damaging silent class — wrong
  damage, element-bonus sign, defense subtraction, status duration — ships green
  because the event *types* are unchanged. A hand-pinned `assert
  calculate_damage(...) == N` fails **even if the `.ambr` is re-baselined**, so it
  is a second, independent sensor. Also: validators today are only ever fed legal
  moves, so rejection paths are untested.
- **Do:**
  - Add `back/tests/unit/test_damage_math.py` — table-driven equality asserts over
    `calculate_damage`, `get_element_bonus` / `get_total_element_bonus`, a sample
    of the element relationships matrix (a few known-good cells, incl. neutral and
    the strongest/weakest), defense subtraction, and the **overkill-reflection**
    branch. Follow the pattern already in `back/tests/unit/test_effects.py`
    (numeric equality asserts + the mutation-drift guard).
  - Add a few `ValidationResult.valid is False` asserts for clearly-illegal moves
    (wrong phase, not-your-turn, target out of range) so the reject path is pinned.
- **Gate:** `cd back && make check` green (pure-engine unit tests; no services, no
  golden change → no `harness-change` label needed).
- **Depends on:** none.

### Step 4b — Pin numbers in the 80-step playthrough + drive a game to terminal (win/lose)
- [ ] **Status:** _not started_
- **Why / failure mode closed:** the existing playthrough fingerprints only event
  class names; numeric payload changes pass silently. And **no test ever reaches
  game-over** — `check_game_end`, `GameEndedEvent`, and the concede path are
  unexercised, so a broken win condition ships green.
- **Do:**
  - Extend `_event_types` (or add a parallel fingerprint) in
    `back/tests/behaviour/test_engine_behaviour.py` to serialize the **load-bearing
    numeric payload** per step (health, damage, defense, element bonus, status
    duration, `winner_id`) with per-run UUIDs stripped, so the golden pins values,
    not just types. Regenerate the `.ambr` deliberately as part of this change.
  - Add a behaviour test that drives one fixed-seed game to a **terminal state**
    (via lethal damage and/or `ConcedeAction`) and asserts `check_game_end` fires
    `GameEndedEvent` with the correct `winner_id`.
- **Gate:** `cd back && make check` green. This step **regenerates the golden**
  (`*.ambr`) → its PR trips the Step 1 guard and is red until a human applies the
  `harness-change` label — expected (a golden change is exactly what deserves human
  eyes); note it in the PR body.
- **Depends on:** none (but its PR needs the `harness-change` label once Step 1 has
  merged).

### Step 5 — Close the "skipped is green" merge hole (paths-filter + ci-ok)
- [ ] **Status:** _not started_
- **Why / failure mode closed:** a PR that edits root `Makefile`, `scripts/**`,
  `docs/**`, or `.claude/**` runs **zero** substantive CI jobs, yet `ci-ok`
  (`ci.yml:234-247`, "skipped is OK") goes green — so harness/loop changes merge
  with no signal. Also a backend-only contract change (events/schemas/routes)
  currently can skip the only cross-stack sensor (e2e).
- **Do:**
  - Broaden `dorny/paths-filter` (`ci.yml:14-31`) so harness/loop paths
    (root `Makefile`, `scripts/**`, `.claude/skills/**`) trigger at least a smoke
    job, and ensure the Step 1 `harness-guard` is in `ci-ok`'s `needs` so an
    unlabeled harness PR can never be green.
  - Require the `e2e` job whenever backend contract surfaces change (add the
    relevant `back/app/**` event/schema/router globs to the frontend filter, or a
    dedicated `contract` filter that gates `e2e`).
- **Gate:** `cd back && make check` unaffected; validate the filter logic by
  reasoning through each path class (docs-only, harness-only, backend-contract).
  Touches `ci.yml` (protected → `harness-change` label).
- **Depends on:** Step 1 (so `harness-guard` exists to wire into `ci-ok`).
- **HUMAN ACTION (not a ralph step), do ASAP:** enable **branch protection** on
  `main` making `ci-ok` a **required** status check (today REST `protection` → 404,
  `rulesets` → `[]`, so every in-repo gate is advisory at merge). Until this is
  set, none of the above is enforced at merge. The loop cannot do this — it needs
  repo-admin.

### Step 6 — Surface + baseline the mutation score (track before gating)
- [ ] **Status:** _not started_
- **Why / failure mode closed:** multi-night silent erosion of *test strength*
  while line coverage holds above 62. Today `mutation.yml` is a no-op sensor
  (`mutmut run || true`, results unparsed, excluded from `make check`).
- **Do:**
  - In `.github/workflows/mutation.yml`, drop the `|| true`, parse `mutmut
    results`, write a summary to `$GITHUB_STEP_SUMMARY`, commit a **baseline**
    score, and **fail on regression** below the baseline (informational → ratchet).
  - Fix the dead command in the comment at `back/pyproject.toml:243`
    (`gt aut run` → `mutmut run`).
- **Gate:** `cd back && make check` unaffected. Touches `mutation.yml` +
  `pyproject.toml` (protected → `harness-change` label).
- **Depends on:** **Step 4a** — gating an empty score before tests assert *values*
  would just baseline near-zero. Sequence after the numeric tests exist.

### Step 7 — Two service/websocket invariant tests (authorization + desync)
- [ ] **Status:** _not started_
- **Why / failure mode closed:** `app.services.*` / `app.websocket.*` (~1.75k LOC)
  carry `ignore_errors=true` (mypy-blind) **and** have zero unit tests; integration
  is one `SELECT 1`. The highest-severity bugs here are an ownership filter dropping
  (any user plays another's deck), the per-player event-visibility filter flipping
  (opponent `card_id` leak), and `GameRunner`'s success-only commit corrupting
  shared state — all with no other sensor.
- **Do:**
  - One integration test asserting `DeckService.get_user_deck` enforces ownership
    (a user cannot load another user's deck).
  - One test asserting `serialize_events_for_player` hides the opponent's hidden
    info (the negative-assertion pattern already used for `RoomSummary` SAFE_KEYS
    in `back/tests/unit/test_room_summary.py`).
  - **Scope to invariants, not the whole layer.** Optional cheap rider: re-enable
    mypy (drop `ignore_errors`) on just `game_runner.py` + `serialization.py` if
    they pass clean.
- **Gate:** `cd back && make check` (+ the integration job's Postgres+Redis for the
  ownership test; marker `integration`).
- **Depends on:** none.

### Step 8 — Frontend: un-exclude the pure game-client TS + add a vitest threshold
- [ ] **Status:** _not started_
- **Why / failure mode closed:** `front/vitest.config.ts` excludes
  `src/babylon-editor/**`, so the pure-TS game client (`ActionBuilder` target/attack
  queries, `GameStateStore.applyServerState` faceUp derivation, `toActionData` wire
  payload) is invisible to the runner with no threshold. The faceUp rule is a real
  hidden-info leak surface. (Lower priority than the engine work: a broken
  target-glow is a *visible* morning bug; wrong damage / a leaked deck is silent.)
- **Do:**
  - Stop excluding the **pure logic** dirs (the `state` / `game` TS under
    `src/babylon-editor/src`, not the 3D toolchain) from vitest collection, and add
    a `thresholds` key to the coverage config so new logic must stay covered.
  - Unit-test `ActionBuilder` (target highlight set, no-defender attack, the
    `STRIP_FIELDS` wire payload) and the `GameStateStore` faceUp rule (opponent
    cards never expose `card_id`).
- **Gate:** the frontend gate green — `cd front && npm run lint && npm run test &&
  npm run deps:check && npm run build`. Touches `vitest.config.ts` (protected →
  `harness-change` label).
- **Depends on:** none.

## Notes / decisions

- **Two highest-leverage items first (this week):** Steps 1–3 (tamper-evident +
  machine-executed gate) and Step 4 (pin engine numbers). Until the gate is a
  machine fact the agent can't edit, every test added below can be silently
  neutered the same night it would have fired; Step 4 closes the most damaging
  silent-correctness hole and survives a golden regeneration.
- **The Step 1 guard is a feature, not a blocker, for the loop.** It is CI-only:
  it never blocks the local `make verify` loop gate, so the loop still runs and
  opens PRs. It only makes any harness-touching PR **red on CI until a human adds
  `harness-change`** — exactly the morning tripwire we want. Steps 1, 3, 4b, 5, 6,
  8 all touch protected paths and so will be red-until-labeled by design.
- **Don't expand e2e; don't chase coverage %.** See "Decided scope" above.
- **Branch protection (Step 5 human action) is the single activation that makes
  every other gate enforceable at merge** — set it the moment a repo-admin can.
