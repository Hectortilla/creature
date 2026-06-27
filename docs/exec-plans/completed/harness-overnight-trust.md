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
- [x] **Status:** ✅ done — 2026-06-22 — added `harness-guard.yml` (no-paths-filter PR guard that hard-fails harness-path edits lacking the `harness-change` label), extended CODEOWNERS to the protected set, added the anti-tamper clause to the ralph SKILL, documented the tripwire + label in `docs/harness.md` — branch `spec/harness-overnight-trust/step-1/tamper-evident` — commit 848ad2e — PR https://app.graphite.com/github/pr/Hectortilla/creature/16
- **Notes for next agent:**
  - **Correction to the `Do` text:** the plan said "add `harness-guard` to `ci-ok`'s `needs`", but GitHub `needs:` can't span workflows and the guard must re-trigger on `labeled`/`unlabeled` (which we don't want to force on the whole CI suite). So `harness-guard` is a **standalone workflow** — enforcement at merge requires branch protection to list **both** `ci-ok` **and** `harness-guard` as required checks. Updated Step 5's human action accordingly.
  - This PR itself touches protected paths (`.github/workflows/**`, `.claude/skills/**`) → its own `harness-guard` check will be **red until a human applies the `harness-change` label**. Expected — it's the tripwire proving itself.
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
- [x] **Status:** ✅ done — 2026-06-22 — `scripts/ralph_loop.py` now re-runs the gate itself after every commit as a machine fact: a non-zero exit sets `gate_failed`, which vetoes `progressed` (the commit/ticked-box no longer counts), increments stalls, surfaces the gate output in the iter log, vetoes "plan complete", and (with `--abort-on-gate-fail`) stops the loop. Gate defaults to `make verify`, overridable via `--gate` (e.g. `make check`). Docs-only commits (every path matches `docs/**/*.md`) skip the gate via a hard allowlist — Makefile/scripts/.claude/code are not docs-only. Verified functionally in a temp git repo (passing gate → progress; failing gate → no progress; docs-only → skipped); `cd back && make check` green (unaffected, 49 passed) — branch `spec/harness-overnight-trust/step-2/driver-runs-gate` — commit 893494b — PR https://app.graphite.com/github/pr/Hectortilla/creature/18
- **Notes for next agent:**
  - **ruff rider — noted why not:** `scripts/` lives at the repo root, outside `back/` where ruff/pytest run (`[tool.ruff]` in `back/pyproject.toml`, `extend-exclude` for alembic/.venv). Wiring `../scripts` into back's ruff would touch the **protected** `back/pyproject.toml` (needs `harness-change` label) for marginal gain on a non-app file. The driver passes `ruff check` cleanly except a **pre-existing** `F821 NoReturn` on line 101 (a lazily-evaluated string annotation already carrying `# type: ignore[name-defined]`) — untouched by this step.
  - The driver gate is intentionally **redundant** with the agent's in-iteration `make verify`: the point is to make "is it green" a machine fact independent of the agent's prose, not to replace the agent's own run.
  - This PR touches `scripts/ralph_loop.py` (protected) → its `harness-guard` check is **red until a human applies the `harness-change` label**. Expected.
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
- [x] **Status:** ✅ done — 2026-06-22 — `Makefile:24` `verify` target no longer forces `-- --retries=2`; it now runs `npm run test:e2e -- --max-failures=1`, so the commit-deciding loop gate inherits Playwright's `retries: CI ? 2 : 0` (0 locally) and never masks a flake (CI keeps its own 2 retries for cross-machine noise). `SKILL.md` rewritten: the stale "auth `@gating` / gameplay `@nongating` runs report-only" lines now state the **whole** e2e suite is `@gating` and blocking and that any e2e failure fails the iteration. Gate green: `make verify` ran the full suite with 0 retries → **9 e2e passed (1.9m)**, `make check` green — branch `spec/harness-overnight-trust/step-3/drop-retry-mask` — commit acd4bcd — PR https://app.graphite.com/github/pr/Hectortilla/creature/19
- **Notes for next agent:**
  - The full e2e suite (9 specs, auth + every gameplay flow) passes with **0 local retries** — no flake masking was happening, so dropping the retries surfaced no hidden flake. If a future iteration sees an e2e flake without retries, fix or report it; do not re-add `--retries`.
  - This PR touches `Makefile` + `.claude/skills/**` (protected) → its `harness-guard` check is **red until a human applies the `harness-change` label**. Expected — it's the tripwire.
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
- [x] **Status:** ✅ done — 2026-06-22 — added `back/tests/unit/test_damage_math.py`: table-driven equality asserts over `get_element_bonus`/`get_total_element_bonus` (directional, stacking, cancelling, neutral), `calculate_damage` (element bonus before defense, physical-vs-magical defense selection, effect modifier, overkill-reflection floor) + a no-drift guard, plus three `RuleValidator` rejection asserts (game-not-in-progress, not-your-turn, wrong-phase). `cd back && make check` green (49 passed, coverage 66.95%, no golden touched) — branch `spec/harness-overnight-trust/step-4a/pin-engine-numbers` — commit 73ce90a — PR https://app.graphite.com/github/pr/Hectortilla/creature/17
- **Notes for next agent:**
  - These are pure-engine tests — **no golden / threshold / harness path touched**, so this PR does *not* need the `harness-change` label (unlike Step 4b, which regenerates the `.ambr`).
  - `calculate_damage(attack, attacker, target, effect_modifier)` ignores `attacker` for the base math — the bonus comes from `attack.element_id` vs `target.element_ids`; effect modifiers are summed by the caller (`build_combat_events`) and passed in, not computed here. Step 4b's numeric fingerprint should pin the *combined* result (attacker/target passive mods + incoming-damage mod) since that's where the real per-step numbers live.
  - The overkill-reflection branch lives in `DamageCalculation.__post_init__` (floors `final_damage` at 0, sets `reflected_damage = abs(...)`); pinned via the `damage 10 / defense 20` row.
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
- [x] **Status:** ✅ done — 2026-06-22 — added a numeric fingerprint (`_event_numbers`) to the playthrough golden: every step now serializes the load-bearing int payload per event (base/element/defense/final damage, remaining/new health, healing amount, status `duration_turns`) plus stable player-id fields (`winner_id`/`loser_id`); per-run uuid instance-ids are excluded so the golden stays deterministic (verified equal across two runs). Regenerated the `.ambr` deliberately (+522 lines, numbers on all 81 steps). Added two terminal tests: `test_concede_drives_game_to_terminal` (concede → single `GameEndedEvent`, `winner_id`/`loser_id` correct, `game_over`) and `test_check_game_end_awards_win_when_board_empty` (empty deck/hand/active → `check_game_end()` returns the opponent). `cd back && make check` green (51 passed, coverage 67.20%) — branch `spec/harness-overnight-trust/step-4b/pin-numbers-terminal` — commit 6ee1093 — PR https://app.graphite.com/github/pr/Hectortilla/creature/20
- **Notes for next agent:**
  - The 80-step fixed-seed playthrough does **not** reach game-over (stops at turn 17, 28/81 steps carry numbers), so the terminal paths (`GameEndedEvent`, concede, `check_game_end`) are covered by the two dedicated tests, not the playthrough golden — that's why the golden has no `GameEndedEvent` numbers row.
  - `instance_id`/card `*_id` are `uuid.uuid4()` (os-random, independent of the game seed) → never put them in a golden; only ints + player ids (`p1`/`p2`) are stable.
  - This PR **regenerates the `.ambr` golden** under `back/tests/behaviour/__snapshots__/*.ambr`, a **protected** path → its `harness-guard` check is **red until a human applies the `harness-change` label**. Expected — a golden change is exactly what deserves human eyes.
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
- [x] **Status:** ✅ done — 2026-06-22 — added a `harness` paths-filter (root `Makefile`, `scripts/**`, `.claude/skills/**`) and a `harness-smoke` job that compiles `scripts/ralph_loop.py` + parses the root `Makefile`, wired into `ci-ok`'s `needs` (+ its result loop). A PR touching only harness/loop paths now runs a real job instead of going vacuously green. Part 2 ("require e2e on backend contract change") was **already satisfied** — `e2e`'s `if` is `frontend || backend`, so any `back/**` change already triggers it; no globs added. Documented the closed hole in `docs/harness.md`. `cd back && make check` green (54 passed, coverage 67.45%), `ci.yml` validated as well-formed YAML, smoke commands verified locally — branch `spec/harness-overnight-trust/step-5/ci-smoke-hole` — commit e317c68 — PR https://app.graphite.com/github/pr/Hectortilla/creature/22
- **Notes for next agent:**
  - **Plan correction:** Step 5's second bullet ("Require the `e2e` job whenever backend contract surfaces change") was a no-op — `e2e` already runs on any `back/**` change (`ci.yml` `if: needs.changes.outputs.frontend == 'true' || needs.changes.outputs.backend == 'true'`). The audit note predates that broadened condition. So I did **not** add contract globs / a `contract` filter; the only real gap was the harness-smoke hole.
  - **docs-only PRs still skip every job** (by design) — `docs/**` matches no filter, so `ci-ok` is still green-on-skip for pure docs changes. That's intended: docs can't break the code gate. The hole the plan cared about (harness/**loop** paths running zero jobs) is what's now closed.
  - The `harness-smoke` job is deliberately light (py_compile + `make -n`); it's a signal-that-something-ran, not a full harness test. If the loop driver grows importable deps worth checking, upgrade it to `uv run python -c "import ..."`.
  - This PR touches `ci.yml` (protected → `.github/workflows/**`) → its `harness-guard` check is **red until a human applies the `harness-change` label**. Expected.
  - **Branch protection (the HUMAN ACTION below) is still unset** and is the single activation that makes `harness-smoke` + `harness-guard` + `ci-ok` actually enforced at merge. Until then this is all advisory.
- **Why / failure mode closed:** a PR that edits root `Makefile`, `scripts/**`,
  `docs/**`, or `.claude/**` runs **zero** substantive CI jobs, yet `ci-ok`
  (`ci.yml:234-247`, "skipped is OK") goes green — so harness/loop changes merge
  with no signal. Also a backend-only contract change (events/schemas/routes)
  currently can skip the only cross-stack sensor (e2e).
- **Do:**
  - Broaden `dorny/paths-filter` (`ci.yml:14-31`) so harness/loop paths
    (root `Makefile`, `scripts/**`, `.claude/skills/**`) trigger at least a smoke
    job. Note: `harness-guard` is a **separate workflow** (cross-workflow `needs`
    is impossible), so it can't be wired into `ci-ok`'s `needs`; instead the
    branch-protection human action below must require it as its own check.
  - Require the `e2e` job whenever backend contract surfaces change (add the
    relevant `back/app/**` event/schema/router globs to the frontend filter, or a
    dedicated `contract` filter that gates `e2e`).
- **Gate:** `cd back && make check` unaffected; validate the filter logic by
  reasoning through each path class (docs-only, harness-only, backend-contract).
  Touches `ci.yml` (protected → `harness-change` label).
- **Depends on:** Step 1 (so `harness-guard` exists to wire into `ci-ok`).
- **HUMAN ACTION (not a ralph step), do ASAP:** enable **branch protection** on
  `main` making **both** `ci-ok` **and** `harness-guard` **required** status checks
  (today REST `protection` → 404, `rulesets` → `[]`, so every in-repo gate is
  advisory at merge). `harness-guard` is a separate workflow and is *not* aggregated
  by `ci-ok`, so it must be listed as its own required check or the Step 1 tripwire
  is bypassable at merge. Until this is set, none of the above is enforced at merge.
  The loop cannot do this — it needs repo-admin.

### Step 6 — Surface + baseline the mutation score (track before gating)
- [x] **Status:** ✅ done — 2026-06-22 — `mutation.yml` now drops `|| true`, runs `mutmut run` → `mutmut export-cicd-stats` → `scripts/mutation_gate.py`, which posts the engine mutation score to `$GITHUB_STEP_SUMMARY` and **fails on regression** below the committed floor in `back/mutation-baseline.json` (45%, measured 52.5% — coverage-conditioned `(killed+timeout)/(killed+timeout+survived+suspicious)`, `no_tests` excluded so it tracks test *strength* not line coverage). Fixed the dead `gt aut run` → `mutmut run` comment. **Also fixed a latent break the iteration surfaced:** the nightly run was silently a no-op — mutmut only copied `app/game/`, so every run died at `ModuleNotFoundError: app.models` and `|| true` masked it; added `also_copy = ["app/"]` + scoped `tests_dir` to the pure-engine corpus, then measured the real score with a full local pass (1310 killed / 85 timeout / 1263 survived / 1025 no_tests of 3683). `cd back && make check` green (54 passed, coverage 67.45%); gate script verified on both the pass (52.48% ≥ 45 → exit 0) and regression (52.48% < 60 → exit 1) paths; `mutants/` gitignored — branch `spec/harness-overnight-trust/step-6/mutation-ratchet` — commit a6b2a3c — PR https://app.graphite.com/github/pr/Hectortilla/creature/23
- **Notes for next agent:**
  - **The nightly mutation run had never actually run.** `mutmut run || true` always died collecting stats (engine imports `app.models`, which wasn't copied into the mutant sandbox) and the score was a vacuous 0 — the `|| true` hid it. So Step 6 also had to make the run *work*: `also_copy = ["app/"]` + a `tests_dir` scoped to the 5 pure-engine unit files + all of `tests/behaviour/` (the other unit files need a live Redis/DB and would break mutmut's hermetic clean-test `-x` pass).
  - **Score metric is coverage-conditioned on purpose:** `no_tests` mutants (uncovered engine lines — 1025 of them, mostly the `association`/`evolution`/`promotion` action files the pure corpus never exercises) are *excluded* from the score, so adding untested engine code doesn't move it (that's `fail_under`'s job). The floor (45%) sits ~7.5pts below the measured 52.5% to absorb timeout-timing variance, since timeouts count as caught and their count drifts run-to-run.
  - **To ratchet up:** raise `min_score` in `back/mutation-baseline.json` as engine tests strengthen. To close the coverage gap, add tests for the uncovered action files and they'll start contributing to the score.
  - This PR touches `mutation.yml` (`.github/workflows/**`) **and** `back/pyproject.toml` (both protected) → its `harness-guard` check is **red until a human applies the `harness-change` label**. Expected — a threshold/CI-gate change is exactly what deserves human eyes. `back/scripts/mutation_gate.py`, `back/mutation-baseline.json`, `.gitignore`, `docs/harness.md` are not protected.
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
- [x] **Status:** ✅ done — 2026-06-22 — added two invariant sensors. `back/tests/integration/test_deck_ownership.py` (marker `integration`): asserts `DeckService.get_user_deck` returns the deck for its owner but `None` for an intruder, and `get_user_decks` is empty for the intruder — so a dropped `user_id` filter (any user plays another's deck) fails the gate. `back/tests/unit/test_event_visibility.py` (marker `unit`): asserts `serialize_events_for_player` masks the opponent's `CardDrawnEvent.card_id` to 0 while keeping the player's own and the `instance_id`, the secret id never appears in the player's JSON payload, and a control proving unfiltered `serialize_events` *does* expose it. `cd back && make check` green (54 passed, was 51); integration test verified against real Postgres (`alembic upgrade head` + `pytest -m integration` → 1 passed) — branch `spec/harness-overnight-trust/step-7/service-invariants` — commit 9705365 — PR https://app.graphite.com/github/pr/Hectortilla/creature/21
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
- **Notes for next agent:**
  - **mypy rider skipped, why:** dropping `ignore_errors` lives in the **protected**
    `back/pyproject.toml`, so the rider would have forced this otherwise-clean PR to
    need a `harness-change` label for marginal gain. The two invariant tests are the
    high-leverage core; left the mypy expansion to the dedicated harness rung in
    `docs/harness.md`. This PR touches **no protected path** → no label needed.
  - The integration test uses `db.flush()` (not `commit`) so the `db_session`
    fixture's `with Session(...)` rolls it back on close — no DB pollution. It needs
    `DATABASE_URL` set + `alembic upgrade head` (CI's `backend-integration` job does
    both); `make check` alone does **not** run it (the `integration` marker is
    deselected), so the morning CI integration job is the enforcing sensor.
  - `serialize_events_for_player` only filters `CardDrawnEvent`; if other
    hidden-info events are added later, extend the mask **and** the test together.
- **Gate:** `cd back && make check` (+ the integration job's Postgres+Redis for the
  ownership test; marker `integration`).
- **Depends on:** none.

### Step 8 — Frontend: un-exclude the pure game-client TS + add a vitest threshold
- [x] **Status:** ✅ done — 2026-06-22 — `front/vitest.config.ts` now collects the Babylon editor's pure-logic dirs (`src/babylon-editor/src/scripts/!(state|game)/**` is the only exclusion left under `scripts/`, so `state/` + `game/` are testable) instead of blanket-excluding `babylon-editor/**`; `node_modules` exclusion broadened to `**/node_modules/**` so the sub-project's own `node_modules` can't leak specs. Added glob-keyed coverage `thresholds` for the two unit-tested files (ActionBuilder ≥95/90/90/95, GameStateStore ≥95/85/90/95) — the rest of `src/lib` stays ungated (no top-level threshold). New tests: `ActionBuilder.test.ts` (target-highlight set + no-defender flag, card/source-id queries, attack lookups, pass/concede, the `STRIP_FIELDS` wire payload) and `GameStateStore.test.ts` (the faceUp hidden-info rule — opponent cards never expose a real `card_id`, plus zone/turn/lifecycle queries). Measured: ActionBuilder 100/96.8/100/100, GameStateStore 98.6/93.9/100/98.6 → threshold gate exits 0. Frontend gate green: `lint` 0 errors, `test` 27 passed, `deps:check` no violations, `build` ok — branch `spec/harness-overnight-trust/step-8/front-game-client-coverage` — commit 72cff70 — PR https://app.graphite.com/github/pr/Hectortilla/creature/24
- **Notes for next agent:**
  - This was the **last** step — the plan is moved to `docs/exec-plans/completed/` in a follow-up commit on this same branch.
  - The two unit-tested files have glob-keyed thresholds; `events.ts` / `game/**` live in the collected dirs but carry no floor (they appear in the report at low %, intentionally ungated). To extend coverage gating, add a glob key per newly-tested file rather than a top-level threshold (the rest of `src/lib` is deliberately ungated).
  - `npm run check` / `build` need `PUBLIC_API_URL` set (no `front/.env`); `npm run test`/`test:cov`/`lint`/`deps:check` run fine sandboxed. The mypy-rider for `game_runner.py`/`serialization.py` (Step 7) is still the only deferred harness item — tracked in `docs/harness.md`.
  - This PR touches `vitest.config.ts` (protected → `front/vitest.config.ts`) → its `harness-guard` check is **red until a human applies the `harness-change` label**. Expected.
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
