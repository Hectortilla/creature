# Harden the harness: enforce the gates, add the semantic sensor, deepen engine correctness

The harness is broad and deterministic (H2) and the overnight loop is now
machine-executed and tamper-*evident* (see
`docs/exec-plans/completed/harness-overnight-trust.md`). Three gaps remain before
an unattended ralph loop can *almost always* be trusted to produce correct code:

1. **The gates are built but not enforced at merge.** Branch protection on `main`
   is unset, so `harness-guard` / `ci-ok` / the coverage + mutation gates are all
   advisory — a red PR can still merge. (Tier 0.)
2. **There is no semantic sensor.** Every control is computational; nothing
   catches "passes every gate but implements the wrong thing". The Claude PR
   reviewer is wired but inert. (Tier 1.)
3. **Engine test *strength* is shallow in absolute terms.** Example tests + the
   numeric golden pin cases we thought of; nothing asserts invariants across the
   input space, and whole action files are untested. (Tier 2.)

This plan closes them in leverage order. Tiers 0–1 are mostly *human switches*
(admin settings, secrets) the loop can't perform — they are listed under **Human
actions** and are **not** ralph steps. The **Steps** section is the
ralph-executable work.

## Current live state (verified 2026-06-27)

- **Branch protection:** none. `GET repos/.../branches/main/protection` → 404;
  `rulesets` → `[]`. Every in-repo gate is advisory at merge.
- **`harness-change` label:** does **not** exist in the repo, so `harness-guard`
  can't be satisfied even for a legitimate change.
- **Claude PR review:** inert — `claude-review.yml` runs only when
  `vars.ENABLE_CLAUDE_REVIEW == 'true'` and needs an `ANTHROPIC_API_KEY` secret.
- **Engine mutation:** floor 45% (`back/mutation-baseline.json`), measured 52.5%;
  **1,263 survived + 1,025 `no_tests` of 3,683** mutants. The action files
  `back/app/game/actions/{association,evolution,promotion}.py` are never exercised
  by the pure corpus.
- **Property testing:** none — `hypothesis` is not a dependency.
- Default branch is `main`; origin is `Hectortilla/creature` (push with the
  personal identity — `GRAPHITE_PROFILE=pers`). The current work `gh` token is
  **not** admin on that repo, so the branch-protection switch must be set from the
  account that owns it (web UI or a `gh` shell authed as that account).

## Human actions (do these yourself — the ralph loop can't; not counted as steps)

These three switches are what make Tiers 0–1 real. Do them once, before/while the
loop runs the Steps below.

- **HA-1 — Enforce the gates at merge (Tier 0, needs repo admin).** Require
  **both** `ci-ok` **and** `harness-guard` as status checks on `main` (they're
  separate workflows — `needs:` can't span workflows, so both must be listed).
  Web UI: *Settings → Branches → Add branch ruleset → Require status checks →
  add `ci-ok` and `harness-guard`*. Or, authed as the repo owner:
  ```bash
  gh api -X PUT repos/Hectortilla/creature/branches/main/protection --input - <<'JSON'
  { "required_status_checks": { "strict": true,
      "checks": [ {"context": "ci-ok"}, {"context": "harness-guard"} ] },
    "enforce_admins": true,
    "required_pull_request_reviews": null,
    "required_linear_history": false,
    "allow_force_pushes": false, "allow_deletions": false,
    "restrictions": null }
  JSON
  ```
  Verify: `gh api repos/Hectortilla/creature/branches/main/protection --jq '.required_status_checks.checks'`.
- **HA-2 — Create the `harness-change` label (Tier 0).** Without it `harness-guard`
  can never be signed off:
  ```bash
  gh label create harness-change -R Hectortilla/creature -c B60205 \
    -d "Human sign-off for a deliberate harness/gate change (required by harness-guard.yml)"
  ```
- **HA-3 — Activate the Claude reviewer (Tier 1, needs the API key).**
  ```bash
  gh secret   set ANTHROPIC_API_KEY   -R Hectortilla/creature   # paste the key
  gh variable set ENABLE_CLAUDE_REVIEW -R Hectortilla/creature --body true
  ```
  Do this **after** Step 1 has pinned/tuned the workflow. Decide advisory vs
  gating: start advisory (don't add `review` to `ci-ok`'s `needs`), promote to
  required only after a green streak proves it isn't noisy — mirror the e2e
  ratchet pattern.

## How to execute

Drive one step per iteration with the **`ralph-iteration`** skill
(`/ralph-iteration harness-enforce-and-deepen`). Pick the highest-leverage
unblocked step, implement only it, leave **`make verify`** green, tick the box,
stack a branch + PR, stop. **Anti-tamper still applies:** never weaken an
assertion, lower a threshold, regenerate a golden, or widen a contract to make a
gate pass — fix the code or stop and report.

**Several steps touch protected paths** (`.github/workflows/**`,
`back/pyproject.toml`) → their PR's `harness-guard` check is **red until a human
applies the `harness-change` label**. That red is the intended morning tripwire,
not a bug; note it in the PR body. Steps touching only `back/tests/**` or
`back/mutation-baseline.json` need **no** label.

## Steps

### Step 1 — Pin & tune the Claude review workflow (Tier 1, code)
- [ ] **Status:** not started
- **Why / failure mode closed:** the only inferential sensor is inert and
  unpinned (`anthropics/claude-code-action@v1` — a moving tag). Before HA-3 flips
  it on, the workflow should be pinned to a verified version with a high-signal,
  repo-specific prompt, so the first real run isn't a surprise.
- **Do:**
  - In `.github/workflows/claude-review.yml`, pin `claude-code-action` to a
    specific released version/SHA after checking its current inputs against
    https://github.com/anthropics/claude-code-action (the `@v1` inputs may have
    drifted). Keep the `if: vars.ENABLE_CLAUDE_REVIEW == 'true'` opt-in gate.
  - Tighten the prompt to the highest-value classes for *this* repo: engine
    purity boundary (`app/game` must not import I/O/DB/web/service), the
    fail-fast / minimal-comment rules in `.claude/rules/`, hidden-info leaks
    (per-player event visibility), and "implements the spec in `README.md`".
    Keep it concise/high-signal (few high-confidence findings).
  - Leave it **advisory** (do not add `review` to `ci-ok`'s `needs`). Record the
    promote-to-gating criterion (green/low-noise streak) in the PR body.
- **Gate:** `cd back && make check` unaffected (CI-config only). Validate the YAML
  (`actionlint` if available). Touches `.github/workflows/**` (protected →
  `harness-change` label on the PR).
- **Depends on:** none. HA-3 turns it on after this merges.

### Step 2 — Add Hypothesis + a first engine invariant suite (Tier 2)
- [x] **Status:** ✅ done — 2026-07-03 — added `hypothesis` dev dep + `tests/unit/test_engine_properties.py` (structural + determinism invariants over Hypothesis-generated legal action sequences) — branch `test/harness-enforce-and-deepen/step-2/engine-invariants` — commit 940fc9b — PR https://app.graphite.com/github/pr/Hectortilla/creature/36
- **Notes for next agent:**
  - Two invariants from the menu were **dropped as genuinely false / risky and must not be re-added blind:** `current_health >= 0` is false (`GameCard.apply_damage` and the `DamageDealtEvent` reducer subtract past zero; `is_alive` = `current_health > 0`), and `current_health <= health` was left out because effect deltas via `CardHealthChangedEvent` aren't provably clamped. The suite asserts the solid ones: **card-instance conservation, zone/no-duplication (each card in exactly its `(owner, zone)` list), turn-ownership, and same-seed+choices determinism** (compared via event-type stream + per-zone census, since `instance_id`s are non-reproducible uuids).
  - **Engine wart surfaced by the property run (not fixed here, out of scope):** while the game is PAUSED for `force_defend`/`forced_swap`, `GameEngine.get_valid_actions` still appends the *active* player's Pass/Concede, but the validator rejects any action except the defender's forced response ("Game is paused, waiting for forced defend action"). So `valid_actions` over-offers illegal actions during a pause. The test models a legal sequence by restricting choices to the required actor (`pending_defender_id or active_player_id`). Worth a follow-up: `get_valid_actions` should not list actions the validator will reject.
  - The suite uses `_build_game` from `test_engine_smoke` (seeded real deck) rather than the empty-deck `empty_state` fixture, because a legal *action sequence* needs a deck to draw from.
- **Why / failure mode closed:** the engine is pure and seeded — ideal for
  property tests — yet there are none. Example tests only pin inputs we imagined;
  the overnight risk is the bug nobody wrote a test for. Invariants catch that
  class across the whole input space.
- **Do:**
  - Add `hypothesis` to the dev dependencies in `back/pyproject.toml`.
  - Add `back/tests/unit/test_engine_properties.py` (marker `unit`, pure engine,
    no DB) using the `empty_state` / `place_card` fixtures in
    `back/tests/conftest.py`. Assert structural invariants that must hold for
    **any** legal action sequence from a seeded start, e.g.:
    - total card count is conserved across zones (no card created or destroyed by
      a move; sum over hand/deck/active/graveyard is constant);
    - no `instance_id` appears in two zones at once (no duplication);
    - health never drops below 0 and never exceeds its max;
    - turn ownership strictly alternates and only the active player can act;
    - replaying the same `GAME_SEED` + action list yields byte-identical events
      (determinism) — and a *different* seed is allowed to differ.
  - Keep cases small/bounded so the suite stays fast in `make check`.
- **Gate:** `cd back && make check` green. Touches `back/pyproject.toml`
  (protected → `harness-change` label); the test file itself is unprotected.
- **Depends on:** none.

### Step 3 — Property tests for the damage / element math (Tier 2)
- [ ] **Status:** not started
- **Why / failure mode closed:** `test_damage_math.py` pins a handful of rows; a
  sign flip or off-by-one outside those rows ships green. Properties pin the whole
  surface.
- **Do:**
  - Extend `test_engine_properties.py` (or a sibling) with property tests over
    `calculate_damage`, `get_element_bonus` / `get_total_element_bonus`, e.g.:
    `final_damage >= 0` always; higher defense never increases `final_damage`
    (monotonicity); element bonus is applied before defense; the element matrix is
    internally consistent (if A beats B then B does not beat A); the
    overkill-reflection floor holds. Cross-check against the live element
    relationships in `back/app/game/elements.py` rather than hand-copying values.
- **Gate:** `cd back && make check` green. Tests only → **no** label needed.
- **Depends on:** Step 2 (Hypothesis present).

### Step 4 — Cover the untested action files (Tier 2)
- [x] **Status:** ✅ done — 2026-07-03 — added `tests/unit/test_actions.py` (28 tests) driving `promotion`/`evolution`/`association` action classes directly: happy-path `validate` + `to_events` field asserts, every rejection `error_code`, `get_valid` enumeration, and the promote `WRONG_PHASE` path via `RuleValidator` — branch `test/harness-enforce-and-deepen/step-4/action-coverage` — commit a55a22b — PR https://app.graphite.com/github/pr/Hectortilla/creature/37
- **Notes for next agent:**
  - Gate run: `cd back && make check` green (all 7 stages). `make verify`'s e2e leg was **not** run: this step adds only a pure backend unit-test file (no production/frontend/config change), so it cannot affect the running-app suite; matches Step 2's precedent and this step's own scoped gate. Tests-only file → **no** `harness-change` label needed.
  - The `place_card` fixture only appends to SUPPORTING/ATTACKING zone lists; HAND/DECK cards must be added to the hand `card_ids` manually — the module's `_in_hand(place_card, state, owner_id, **fields)` helper does this. Reuse it for Step 5 measurements.
  - Two rejection branches were intentionally left uncovered as low-value/hard-to-craft: association's `ASSOCIATION_TARGET_FILTER` (needs a filter-atom that emits errors) and the direct-from-hand association source path (`association_allows_direct_from_hand`, needs a `cambio_de_guardia`/`playable_directly_from_hand` script atom). Worth adding in a follow-up if Step 5's mutation run shows survivors there.
  - Step 5 can now measure these three files; expect the `no_tests` bucket for `actions/{association,evolution,promotion}.py` to shrink and surviving/killed counts to appear.
- **Why / failure mode closed:** `back/app/game/actions/{association,evolution,
  promotion}.py` are in the `no_tests` bucket (part of the 1,025 uncovered
  mutants) — their rules can break completely and silently. Coverage here both
  finds real bugs and lets the mutation score start measuring them.
- **Do:**
  - Add direct unit tests (`back/tests/unit/`) driving each action through the
    engine from a crafted `empty_state` + `place_card` setup: assert the produced
    events and load-bearing numbers (equality asserts, like `test_damage_math.py`
    and `test_effects.py`), plus the validator rejection paths for each
    (illegal source/target/phase).
  - If any file needs live Redis/DB to exercise, scope that part to an
    `integration`-marked test instead; keep the pure-rule paths in `unit`.
- **Gate:** `cd back && make check` green (+ the `integration` job for any
  DB-backed test). Tests only → **no** label.
- **Depends on:** none (independent of 2/3; can interleave).

### Step 5 — Ratchet the engine mutation floor after the new tests land (Tier 2)
- [ ] **Status:** not started
- **Why / failure mode closed:** Steps 2–4 should kill currently-surviving
  mutants; the floor (45%) must move up to *lock in* that strength, else it can
  silently erode back down.
- **Do:**
  - Re-measure the engine mutation score locally (`cd back && mutmut run &&
    mutmut export-cicd-stats && uv run python scripts/mutation_gate.py`), confirm
    it rose, and raise `min_score` in `back/mutation-baseline.json` to sit just
    below the new measured value (leave the documented timeout-variance margin).
    Update the `comment` with the new measurement + date.
  - Do this as the **last** Tier-2 step so the floor reflects all the new tests.
  - **Decision to make (from Step 2):** whether to add `tests/unit/test_engine_properties.py`
    to `[tool.mutmut].tests_dir`. Pro: property tests are strong mutant killers. Con:
    the randomized Hypothesis suite is slower and a mutant killed on only some examples
    classifies nondeterministically across mutmut runs — which can destabilize the floor.
    If added, pin its examples (fixed seed / `derandomize`) so classification is stable.
- **Gate:** the mutation gate script exits 0 at the new floor; `cd back && make
  check` unaffected. `mutation-baseline.json` is **unprotected** (no label); do
  **not** also edit `mutation.yml` (protected) unless necessary.
- **Depends on:** Steps 2–4.

### Step 6 — Record the enforced end-state in `docs/harness.md` (close the loop)
- [ ] **Status:** not started
- **Why / failure mode closed:** the harness is owned like code — when the
  enforcement switches and the new sensor class land, the doc must say so, or the
  next agent re-discovers the gap.
- **Do:**
  - Update `docs/harness.md`: branch protection now requires `ci-ok` +
    `harness-guard` (HA-1); the Claude reviewer is the active inferential sensor
    (advisory/gating per HA-3 + Step 1); property-based testing is now part of the
    engine corpus; bump the mutation-score paragraph to the new floor. If the
    enforcement is fully on, note the maturity move toward **H3**.
- **Gate:** docs-only (`docs/**/*.md`) → driver skips the gate; markdown
  link-check (`docs.yml`) stays green. **No** label.
- **Depends on:** HA-1/HA-3 done and Steps 1–5 merged (so the doc states facts,
  not intentions).

## Notes / decisions

- **Ordering rationale.** HA-1/HA-2 first — they're free and make every existing
  gate real; without them the rest is advisory. HA-3 + Step 1 add the missing
  sensor *class* (semantic) cheaply. Steps 2–5 are the real coding effort and the
  best catcher of *unanticipated* engine bugs. Step 6 records it.
- **Deliberately out of scope (same calls as the prior plan):** expanding E2E
  (most expensive per bug, Chromium-only, "proves wiring not rules") and chasing
  the `fail_under` line-coverage %. Engine *invariants* and the semantic reviewer
  are higher leverage per token.
- **Possible follow-ons (not in this plan):** extend the mutation/coverage ratchet
  to a boundary package (`services`/`websocket`); promote the Claude reviewer to a
  required check once it proves low-noise; promote `npm run check` (svelte-check)
  and `npm run knip` to gating once their backlogs clear.
