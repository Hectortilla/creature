# Promote the gameplay E2E flows `@nongating` → `@gating`

The next ratchet rung for the running-app sensor, after
[`../completed/e2e-verification-harness.md`](../completed/e2e-verification-harness.md)
(game start + 3D board) and
[`../completed/e2e-gameplay-harness.md`](../completed/e2e-gameplay-harness.md)
(play_card / pass / swap / attack). Those plans deliberately left all 6 gameplay
specs `@nongating` — run everywhere, block nowhere — until they prove stable.
This plan flips them to `@gating` so a gameplay regression blocks merges (and the
ralph loop), in CI **and** in `make verify`, at once.

## 1. Goal & why this exists

`@gating` means "blocks everywhere (CI + the `make verify` loop gate)";
`@nongating` means "runs everywhere, blocks nowhere". Today the 6 gameplay specs
are `@nongating`, so a real gameplay break only shows as a non-blocking diff.
The ratchet — documented in [`../../harness.md`](../../harness.md) — promotes
them once they earn it. This plan makes that promotion an executable, gated
sequence rather than a someday-bullet.

## 2. Promotion criterion (the "green streak") — the gate on Step 2

Defined in [`../../harness.md`](../../harness.md): the `@nongating` e2e step has
passed on **≥ 10 consecutive `main` CI runs** with no flaky-retry passes — and
the ralph loop's report-only `@nongating` leg has flagged no failure across that
window. **Step 2 must not be done until this holds.** If it doesn't, bail per
`ralph-iteration` skill step 4 (a step you cannot satisfy is a step you cannot
mark done) and report the current streak.

**How to measure (read the Playwright summary, not the step conclusion).** The
`@nongating` step runs under `continue-on-error: true`, which rewrites its
conclusion to `success` even when Playwright failed — so `gh run list` and the
step/job status are *blind* to a `@nongating` regression and must not be used to
judge the streak. Instead, per run on `main`, read the actual Playwright result:
- `gh run view <id> --log` (or `--job <e2e-job-id> --log`) and parse the final
  Playwright summary line (`N passed` with **no** `failed`/`flaky`), **or**
- `gh run download <id> -n playwright-report` and read the report's results.

A run counts toward the streak only when that summary is clean (no failures, no
flaky-retry passes). A green step conclusion alone is not evidence.

## 3. What's in the way (constraints)

- ~~**`game.e2e` has no Linux screenshot baseline.**~~ ✅ resolved by Step 1:
  `front/e2e/game.e2e.ts-snapshots/board-chromium-linux.png` is now committed, and
  `game.e2e.ts`'s `toHaveScreenshot` carries a per-call `timeout: 30_000` so the
  software-WebGL canvas stabilises within budget on Linux CI as well.
- **You can't generate a `-linux.png` on macOS** — Playwright suffixes baselines
  by platform, so a Mac run only ever writes `-darwin.png`. Step 1 must run on
  Linux (Docker or CI).
- **Tag form.** The 6 gameplay specs carry the tag inside the `describe` *title*
  (e.g. `test.describe("@nongating game start + board render", …)`), whereas
  `auth.e2e.ts` uses the option form `{ tag: "@gating" }`. `--grep` matches both.
- **`pointer.e2e.ts` is the live blocker (~45% CI flake).** Measured 2026-06-13:
  it is the *only* gameplay spec resetting the §2 streak. New **Step 1.5** must
  settle it before Step 2 is reachable.

## Steps

### Step 1 — Commit the Linux `game.e2e` screenshot baseline
- [x] **Status:** ✅ done — 2026-06-13 — generated + committed `board-chromium-linux.png` via the Dockerized Playwright image (`v1.60.0-jammy`, amd64) with `--update-snapshots`; a clean verify run inside Docker re-matched it (no drift). `make verify` green on macOS (auth `@gating` 3 passed; all 6 `@nongating` passed incl. `game.e2e` darwin). — branch `spec/e2e-gating-promotion/step-1/linux-baseline` — commit `136dcee` — PR **https://github.com/Hectortilla/creature/pull/3** (DRAFT, awaiting merge). **Push blocker RESOLVED (2026-06-13): the branch is on `origin` and PR #3 is open. Its CI `e2e` job (run `27462428028`, job `81178599568`) is GREEN, and the actual Playwright summary — not the `continue-on-error`-masked conclusion — confirms the gate: `auth smoke (gating) 3 passed` + `game + 3D smoke (non-gating) 6 passed`, including `game.e2e.ts › board render ✓` on Linux. So the committed `-linux.png` matches on Linux CI with no diff. The remaining action is a human one: mark PR #3 ready and merge it to `main` (it's a draft for morning review).**
- **Notes for next agent:**
  - **A per-call `timeout: 30_000` on `game.e2e.ts`'s `toHaveScreenshot` was required and is now committed.** Under software-WebGL the canvas needs >5 s (the default) to hold two stable frames, so the baseline-write *and every comparison* (CI included) need the longer budget. A prior attempt put `expect: { toHaveScreenshot: { timeout } }` in `playwright.config.ts` — that key does **not** exist on the config type (only `threshold`/`maxDiff*`/`animations`/…), so it was a silent no-op; the per-call option is the correct, type-checked place. Step 2 inherits this fix automatically.
  - The Dockerized build OOMs at Node's ~2 GB default heap (babylon-editor + fluentui bundle); set `NODE_OPTIONS=--max-old-space-size=4096` if regenerating in a container.
  - ✅ Confirmed (2026-06-13) on PR #3's CI `e2e` job (run `27462428028`): `game.e2e`'s screenshot matches on Linux (no diff) — Playwright summary `6 passed` non-gating incl. `board render ✓`. Safe to flip in Step 2 once PR #3 merges and the §2 streak accrues.
- Generate and commit `front/e2e/game.e2e.ts-snapshots/board-chromium-linux.png`
  so `game.e2e`'s `toHaveScreenshot` can pass on Linux CI. Two viable routes:
  - **Docker (preferred, reproducible locally):** run the `@nongating` suite
    inside the official Playwright Linux image
    (`mcr.microsoft.com/playwright:vX.Y.Z-jammy`, version-matched to
    `front/package.json`) with `--update-snapshots`, mounting the repo so the
    written `-linux.png` lands in the tree. Postgres + Redis must be reachable
    from the container (compose them in, or point `DATABASE_URL`/`REDIS_URL` at
    host services). The `clio-diagnose-docker` skill can help inspect the env.
  - **CI artifact:** on a CI run, the missing-baseline comparison writes the
    actual render into `front/test-results/`, uploaded as `playwright-report`
    (see `.github/workflows/ci.yml`). `gh run download <id> -n playwright-report`,
    lift the actual PNG, and commit it as the baseline.
- Commit **only** the new `-linux.png`; do not touch the `-darwin.png`.
- **Gate:** `make verify` still green (darwin baseline unaffected); the new file
  is committed. CI's `@nongating` run shows game.e2e's screenshot matching on
  Linux (no diff) — confirm on the resulting PR's `e2e` job artifact.
- Depends on: none.

### Step 1.5 — Stabilize the flaky `pointer.e2e.ts` real-pointer spec
- [x] **Status:** ✅ done — 2026-06-13 (7th iteration) — folded the real click's
  *projection + pick + click + outcome-wait* into one `toPass` retry so a click
  that misses the still-animating fan-in mesh re-projects on the card's CURRENT
  position and re-clicks, instead of failing the fixed 10 s `waitForState`. Each
  attempt re-resolves a playable card whose projected centre picks back to itself,
  clicks it, then waits ≤5 s for it to reach SUPPORTING (`.then(…, …)` turns that
  wait's timeout into a re-project retry, not a throw); a `clicked` set
  short-circuits once any prior click lands so we don't keep playing cards while a
  WS confirmation is in flight. `make verify` green (auth `@gating` 3 passed; all
  6 `@nongating` passed incl. `pointer.e2e.ts` ✓ 14.5 s); local `npm run test:e2e
  -- --grep pointer` green (18.2 s, no flaky-retry). Touches only
  `front/e2e/pointer.e2e.ts`. — branch
  `spec/e2e-gating-promotion/step-1.5/stabilize-pointer` — commit `12bc545` —
  PR **https://github.com/Hectortilla/creature/pull/10**
- **Notes for next agent:** the macOS CI flake won't reproduce locally, so green
  here proves *no regression*, not the fix — the proof is the §2 streak now
  accruing on `main` **without** `pointer.e2e.ts` resetting it. **The pre-fix
  streak measurements below (Step 2 table, 1/10) are now stale**: the fix only
  lands on `main` once this PR (and the Step 2 doc-stack) merge, so the streak
  re-baselines to 0 at that merge and must reach **10 consecutive clean `main`
  runs with the fix in place** before Step 2's flip. Re-measure from the first
  post-merge `main` run forward, not from the old reference.
  - **✅ First Linux-CI confirmation the fix holds (2026-06-13, 8th iteration).**
    PR #10's own CI run `27472476991` (e2e job `81205799715`, sha `90a48c9`) ran
    the still-`@nongating` suite on Linux software-WebGL and came back **clean, no
    flaky-retry**: `auth (gating) 3 passed` + `game+3D (non-gating) 6 passed`,
    incl. `pointer.e2e.ts:22 › real-pointer play_card → SUPPORTING ✓ (25.8s)`.
    That's the *same Linux environment* that flaked ~45% pre-fix, so it's the
    first real evidence the `toPass`-wrapped click works — not just macOS
    no-regression. It is **one** clean Linux run, not the §2 streak (still needs
    10 consecutive clean `main` runs with the fix merged), but it materially
    de-risks Step 2 and the merge.
- **Root cause (grounded in the CI logs).** The failure is always
  `page.evaluate: Error: BoardController: waitForState timed out after 10000ms`
  at `pointer.e2e.ts:90–96` — i.e. after the real `actor.mouse.click(target.x,
  target.y)` (line 87) the clicked card never reaches `SUPPORTING`, so the in-page
  `waitForState` (default `DEFAULT_TIMEOUT_MS = 10_000`, `E2EHarness.ts:33`) times
  out. The likely mechanism: `target` (the projected screen point) is resolved
  inside the `toPass` block at lines 53–75, but the post-deal fan-in animation is
  still moving the hand meshes; under CI's slow software-WebGL the mesh drifts
  between *resolve* and *click*, so `scene.pick` misses (or picks a non-playable
  card), `play_card` never dispatches, and the wait times out. In the hard-fail
  run it missed on all 3 retries (run `27469376648`), so it is not mere slowness —
  bumping the `waitForState` timeout alone will **not** fix it.
- **Do** — make the real click resilient to the fan-in race. Prefer the minimal
  robust option; do not just raise the timeout:
  1. Wrap the *click + outcome* in a single `toPass` retry: re-project
     (`screenPositionOf`) and re-pick (`cardAtScreenPoint`) the target, click, then
     check `SUPPORTING` within a short per-attempt `waitForState`, so a missed
     click re-projects and re-clicks instead of failing; **or**
  2. wait for the hand fan-in to settle (scene idle / a stable-coords poll) before
     projecting, so the resolved coords are still valid at click time.
- **Acceptance:** the spec stops resetting the streak — `pointer.e2e.ts` passes
  with **no** flaky-retry across the §2 window of consecutive `main` runs. Locally
  it must stay green (the CI flake won't reproduce on macOS, but a regression
  would): `cd front && npm run test:e2e -- --grep pointer`.
- **Gate:** `make verify` green; the change touches only `front/e2e/pointer.e2e.ts`
  (and, if option 2 needs it, a scene-idle helper in `front/e2e/`).
- Depends on: none (independent test fix; unblocks the §2 streak for Step 2).

### Step 2 — Flip the 6 gameplay specs to `@gating` (CI + loop)
- [ ] **Status:** ⛔ **BLOCKED on a human merge → then the §2 green streak**
  (Step 1.5 is ✅ done — `pointer.e2e.ts` was the sole streak-resetting spec and
  is fixed, and as of the 8th iteration the fix is **confirmed clean on Linux CI**
  via PR #10's run `27472476991`; see Step 1.5 notes). As of 2026-06-13 (8th
  iteration) the streak is **0 / 10 against the post-fix baseline**: the fix is
  not yet on `main` (PR #10 + the #9 doc-base are open **drafts**), so no post-fix
  `main` run exists and `main` is unchanged at `c27583f` with the same 11 runs as
  iteration 7. **The only action that can advance this plan now is a human: mark
  PRs #9 + #10 ready and merge them to `main`.** Until then the loop can only
  re-confirm an unchanged state (churn) — do not spend iterations here. After the
  merge, the streak re-baselines to 0; re-measure from the first post-merge `main`
  run forward and flip only when **10 consecutive clean `main` runs with the fix
  in place** hold. The pre-fix table below (1/10, ~45% pointer flake) is
  **historical**.
- **🛑 Before spending an iteration here, re-measure the §2 streak from the actual
  Playwright summaries** (not the `continue-on-error`-masked conclusions). One
  pass that prints the per-run verdict:
  ```
  git fetch -q origin main
  for id in $(gh run list --branch main --workflow CI --limit 30 \
        --json databaseId,conclusion --jq '.[]|select(.conclusion=="success").databaseId'); do
    job=$(gh run view "$id" --json jobs --jq '.jobs[]|select(.name=="e2e").databaseId')
    echo "$id: $(gh run view "$id" --job "$job" --log | grep -oiE '[0-9]+ (passed|failed|flaky)' | tr '\n' ' ')"
  done
  ```
  A run counts toward the streak **only** if its summary is `3 passed … 6 passed`
  with **no** `failed` and **no** `flaky`. Cancelled runs neither count nor break
  the chain. Flip only once ≥10 *consecutive* clean completed `main` runs hold.
- **Measured 2026-06-13 (bail, do not flip) — streak 1/10, blocker identified.**
  Read the actual Playwright summary of the 11 completed `main` runs from the
  reference forward; chronological verdicts:
  | # | run | e2e job | verdict |
  |---|-----|---------|---------|
  | 1 | 27464331154 | 81183867858 | ✅ 3+6 clean |
  | 2 | 27465971910 | 81188272440 | ❌ pointer **failed** (3 retries) |
  | 3 | 27466148166 | 81188713171 | ⚠️ pointer **flaky** |
  | 4 | 27466439604 | 81189480499 | ⚠️ pointer **flaky** |
  | 5 | 27466680211 | 81190124526 | ✅ 3+6 clean |
  | 6 | 27467103085 | 81191271127 | ✅ 3+6 clean |
  | 7 | 27467489913 | 81192315332 | ✅ 3+6 clean |
  | 8 | 27467924307 | 81193472137 | ⚠️ pointer **flaky** |
  | 9 | 27468460028 | 81194910942 | ✅ 3+6 clean |
  | 10 | 27469376648 | 81197401449 | ❌ pointer **failed** (3 retries) |
  | 11 (tip) | 27470147237 | 81199497284 | ✅ 3+6 clean |

  Run #10 (immediately before the tip) hard-failed, so the **consecutive** clean
  streak ending at the tip is **1**; the longest clean sub-run anywhere in the
  window is 3 (runs #5–7). Every reset is `pointer.e2e.ts` — the other five specs
  passed in all 11 runs. **Order of operations for the next agent:** (1) do
  Step 1.5 to stop `pointer.e2e.ts` resetting the streak; (2) re-measure per the
  command above; (3) flip only once ≥10 consecutive clean `main` runs hold; (4)
  until then, bail per skill step 4.
- **Decision / fallback to weigh (grounded in the data above).** `pointer.e2e.ts`
  is ~45% flaky and is a hard WebGL/two-browser timing flake; if Step 1.5 does not
  settle it within a couple of iterations, consider **splitting the promotion**:
  flip the five provably-stable specs (`attack, game, gameplay, phase, swap`) to
  `@gating` now and keep `pointer.e2e.ts` `@nongating` until it is fixed. This
  delivers most of the gate value immediately. Not done unilaterally here because
  it changes the plan's "no `@nongating` tier remains" end-state; flag for the
  human if Step 1.5 stalls.
- Then make the promotion in one change:
  1. **Tags** — flip `@nongating` → `@gating` in the `describe` of all six:
     `front/e2e/{attack,game,gameplay,phase,pointer,swap}.e2e.ts`. Prefer
     normalising to the option form `{ tag: "@gating" }` to match
     `auth.e2e.ts`; a title-string swap also works for `--grep`.
  2. **CI** (`.github/workflows/ci.yml`) — the gameplay specs now gate, so drop
     the separate `continue-on-error` "non-gating" step and run the whole suite
     blocking. Simplest: replace the two e2e steps with one
     `- run: npm run test:e2e` (everything is `@gating` now), keeping the
     report/trace upload. Refresh the surrounding comment (lines ~137–143,
     ~199–209) so it no longer describes a split.
  3. **`make verify`** (root `Makefile`) — drop the report-only `@nongating`
     line; the target becomes `verify: check` + a single hard
     `cd front && npm run test:e2e -- --retries=2` (the whole suite now blocks).
  4. **Docs** — update [`../../harness.md`](../../harness.md) (the sensor-table
     row, the split-gating prose, and tick the promotion rung ✅), `AGENTS.md`
     (the running-app + loop-gate rows), and `front/AGENTS.md` to say **all** e2e
     specs gate now (no `@nongating` tier remains).
- **Gate:** `make verify` hard-gates the whole suite (a forced gameplay failure
  blocks it); CI `e2e` job is green and blocking; `grep -rn "@nongating" front/e2e`
  returns nothing.
- Depends on: Step 1, **Step 1.5** (stabilise `pointer.e2e.ts`), **and** the
  green-streak criterion (§2).

### Step 3 — Complete the plan
- [ ] **Status:** not started
- Move this file to `../completed/`. Confirm the harness.md promotion rung is
  ticked and no stale `@nongating` references remain in the docs.
- **Gate:** docs link-check green (`lychee --offline`).
- Depends on: Step 2.

## Changelog

- **2026-06-13** — Ralph iteration (8th): **confirmed the Step 1.5 fix holds on
  Linux CI, and pinned the plan's true blocker — a human merge.** No step was
  flippable: `main` is unchanged at `c27583f` with the *same 11 runs* iteration 7
  measured, and the Step 1.5 fix (`90a48c9`) is not on `main` (PRs #9 + #10 are
  open **drafts**), so the §2 streak is 0/10 and cannot accrue. New, decision-
  relevant evidence: PR #10's own CI run `27472476991` (e2e job `81205799715`)
  ran the suite on Linux software-WebGL **clean, no flaky-retry** —
  `pointer.e2e.ts ✓ (25.8s)`, the first non-macOS proof the `toPass`-wrapped click
  works (the ~45%-flake environment now passes). Recorded that proof on Step 1.5,
  and rewrote Step 2's status to say the *only* plan-advancing action left is a
  human merging the #9/#10 stack to `main` — the loop can otherwise only re-confirm
  an unchanged state. Bailed on the flip per skill step 4 (0 ≪ 10). Plan-doc edits
  only — branch `spec/e2e-gating-promotion/step-2/pointer-fix-ci-confirmed`, PR
  **https://github.com/Hectortilla/creature/pull/11**.
- **2026-06-13** — Ralph iteration (7th): **did Step 1.5 — stabilised
  `pointer.e2e.ts`**, the spec the 6th iteration proved was the sole §2
  streak-resetter (~45% CI flake, always `BoardController: waitForState timed out`
  after a real click missed the still-animating fan-in mesh). Fix: folded the
  click's *projection + pick + click + a short ≤5 s outcome-wait* into one
  `toPass` retry, so a missed click re-projects on the card's current position and
  re-clicks rather than failing a fixed 10 s wait; a `clicked` set short-circuits
  once any click lands. `make verify` green end-to-end (backend check, frontend
  unit 8 passed, auth `@gating` 3 passed, all 6 `@nongating` passed incl.
  `pointer.e2e.ts` ✓); local `--grep pointer` green. Marked Step 2 blocked **only**
  on the streak now (Step 1.5 cleared); noted the pre-fix 1/10 table is historical
  and the streak re-baselines to 0 at merge. Code change touches only
  `front/e2e/pointer.e2e.ts`. — branch
  `spec/e2e-gating-promotion/step-1.5/stabilize-pointer`, PR **https://github.com/Hectortilla/creature/pull/10**.
- **2026-06-13** — Ralph iteration (6th): **un-parked Step 2 and found the real
  blocker.** `origin/main` *has* advanced (tip now `c27583f`, 10+ new completed
  CI runs since the reference) — so the prior "circular loop, `main` never
  advances" parking rationale was wrong. Measured the §2 streak from the **actual
  Playwright summaries** of the 11 completed `main` runs from the reference
  forward: **1/10** (run #10, immediately before the tip, hard-failed; longest
  clean sub-run is 3). Every single reset is one spec — `pointer.e2e.ts:28`
  flaked/failed in **5 of 11 runs (~45%)** with `BoardController: waitForState
  timed out after 10000ms`; the other five gameplay specs passed in all 11. Added
  **Step 1.5** (stabilise `pointer.e2e.ts` — the fan-in coordinate race makes the
  real `scene.pick` click miss under CI software-WebGL) as the new unblocked,
  highest-leverage work, and made Step 2 depend on it. Recorded a split-promotion
  fallback (gate the 5 stable specs, keep pointer `@nongating`) if Step 1.5 stalls.
  Bailed on the flip (1 ≪ 10). Plan-doc edits only — branch
  `spec/e2e-gating-promotion/step-2/pointer-flake-blocker`, PR
  **https://github.com/Hectortilla/creature/pull/9**.

- **2026-06-13** — Ralph iteration (5th): re-measured the §2 streak — **still
  1/10, `origin/main` unchanged** (tip `a538545`, newest CI run still
  `27464331154`; no new completed `main` run since the 4th iteration). Rather than
  emit a 5th identical "still 1/10" recheck, **parked Step 2**: added a one-command
  precondition gate (don't re-run while the newest `main` CI run id is still
  `27464331154`) and documented *why* the loop is circular — the only PRs this
  loop produces are non-self-merging draft rechecks, so re-measuring an unchanged
  `main` is pure churn that can never advance the streak; the streak must accrue
  from real PRs merging to `main`. No tags/CI/Makefile/docs touched — plan-doc
  edits only — branch `spec/e2e-gating-promotion/step-2/park-streak-loop`, PR
  **https://github.com/Hectortilla/creature/pull/8** (stacked on #7).
- **2026-06-13** — Ralph iteration (4th): re-measured the §2 streak — **still
  1/10, no change**. `origin/main`'s tip is unchanged (`a538545`, run
  `27464331154`); its e2e job's Playwright summary is still clean (`gating 3
  passed` + `non-gating 6 passed`, no failed/flaky). No new completed `main` CI
  run exists since the 3rd iteration because the stacked doc-PRs (#6 + this one)
  haven't merged yet, so `main` hasn't advanced. Clarified on Step 2 that the
  streak advances **only** as these stacked PRs merge to `main` (each = one fresh
  full-suite `main` run), and that ~9 more are needed. Bailed on the flip again
  (1 ≪ 10). No tags/CI/Makefile/docs touched — plan-doc edits only — branch
  `spec/e2e-gating-promotion/step-2/streak-recheck-1-of-10`, PR
  **https://github.com/Hectortilla/creature/pull/7**.
- **2026-06-13** — Ralph iteration (3rd): Step 1 is now **fully merged** to
  `main` (PRs #3/#4/#5 all merged; squash commit `1a66b6f` carries the Linux
  baseline — `origin/main` now has both `-darwin.png` and `-linux.png`). Verified
  the **first post-merge `main` CI run** carrying the baseline (sha `a5385456`,
  run `27464331154`, e2e job `81183867858`) is clean: Playwright summary `auth
  (gating) 3 passed` + `game+3D (non-gating) 6 passed`, no failed/flaky — so the
  baseline matches on `main`, not just PR #3's branch. The §2 streak has
  **started: 1/10**. Bailed on Step 2 again (1 ≪ 10), but corrected its blocker
  from "PR #3 awaiting human merge" → "merged; streak accruing, 1/10" and rewrote
  the order-of-ops accordingly. No tags/CI/Makefile/docs touched — plan-doc edits
  only — branch `spec/e2e-gating-promotion/step-2/streak-1-of-10`, PR
  **https://github.com/Hectortilla/creature/pull/6**.
- **2026-06-13** — Ralph iteration (2nd): the push blocker that dominated this
  plan is **resolved** — Step 1's branch is on `origin`, PR #3 (and Step 2's note
  PR #4) are open. Verified Step 1's previously-unconfirmable CI gate: PR #3's
  `e2e` job (run `27462428028`) is green and its Playwright summary is clean on
  Linux (`game.e2e › board render ✓`, 6 non-gating passed, 3 gating passed) — the
  committed `-linux.png` matches CI with no diff. Re-measured the §2 streak = **0**
  (Step 1 still a DRAFT, `136dcee` not on `origin/main`, latest `main` run still
  predates the baseline). Bailed on Step 2 again, but corrected its blocker from
  "unpushed/1Password locked" → "PR #3 awaiting human merge". No tags/CI/Makefile/
  docs touched. Plan-doc edits only — branch
  `spec/e2e-gating-promotion/step-2/ci-gate-confirmed` (stacked on Step 2's note
  branch), commit `5b8a6a3`, PR **https://github.com/Hectortilla/creature/pull/5**.
- **2026-06-13** — Ralph iteration: bailed on Step 2 per skill step 4 (cannot
  satisfy → cannot mark done). Measured the §2 streak = **0** (latest `main` run
  `6f0c9c9` shows `@nongating` `game.e2e` failing on the missing Linux baseline,
  masked by `continue-on-error`). Root cause unchanged: Step 1's baseline is
  unpushed (1Password SSH agent locked). Recorded the measurement + order-of-ops
  on Step 2 so the next iteration doesn't re-derive it. No tags/CI/Makefile/docs
  touched — flipping prematurely would gate a spec that currently fails on Linux.
  These edits are committed on branch
  `spec/e2e-gating-promotion/step-2/blocked-streak-note` (stacked on Step 1's
  branch); **its PR is pending on the same 1Password SSH blocker** — `gt submit
  --stack` push fails with `Permission denied (publickey)`. Unlock 1Password,
  then `GRAPHITE_PROFILE=pers gt submit --stack --no-edit` pushes both branches.

## Notes / decisions

- **Why gated, not flipped now:** the specs are historically flaky under load
  (WebGL/two-browser timing); the ratchet protects unrelated PRs from that flake
  until a real green streak proves it's settled. The loop running `make verify`
  every iteration (now report-only on `@nongating`) is what *produces* the streak
  evidence this plan consumes.
- **One tag, one flip:** because `make verify` mirrors CI, flipping the tag moves
  a spec into the hard gate in **both** places simultaneously — there is no
  separate "promote in the loop" step.
