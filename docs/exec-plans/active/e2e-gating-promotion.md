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

### Step 2 — Flip the 6 gameplay specs to `@gating` (CI + loop)
- [ ] **Status:** blocked — green streak = **1 / 10** as of 2026-06-13. Cannot proceed.
- **First, confirm the green streak (§2).** If unmet, bail and report — do not
  proceed.
- **Measured 2026-06-13 (bail, do not flip):** streak is **1 of 10**. Step 1 is
  now **merged** to `main` — PR #3 merged at 10:32Z (squash commit `1a66b6f`),
  and `git merge-base --is-ancestor 136dcee origin/main` → YES;
  `front/e2e/game.e2e.ts-snapshots/` on `origin/main` now carries **both**
  `-darwin.png` **and** `-linux.png`. The prior "DRAFT / awaiting human merge"
  blocker is **gone**. The first post-merge `main` CI run carrying the baseline
  (sha `a53854561849`, run `27464331154`, e2e job `81183867858`) is **clean** —
  Playwright summary `auth smoke (gating) 3 passed` + `game + 3D smoke
  (non-gating) 6 passed`, **no** failed/flaky (read the summary, not the
  `continue-on-error`-masked `success` conclusion). So the baseline matches on
  `main` itself, not just on PR #3's branch — the streak has **started** and
  stands at **1/10**. (The two intermediate post-merge runs — `1a66b6f` #3 and
  `91367db` #4 — were **cancelled** by superseding pushes within ~3 min, so they
  neither count nor break the chain; `a5385456` #5 is the first that ran to
  completion.) **Order of operations for the next agent:** (1) count the §2
  streak forward from run `27464331154` — each new clean `main` run is +1; (2)
  flip only once ≥10 consecutive clean completed `main` runs hold (no
  failed/flaky in the Playwright summary); (3) until then, bail per skill step 4.
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
- Depends on: Step 1 **and** the green-streak criterion (§2).

### Step 3 — Complete the plan
- [ ] **Status:** not started
- Move this file to `../completed/`. Confirm the harness.md promotion rung is
  ticked and no stale `@nongating` references remain in the docs.
- **Gate:** docs link-check green (`lychee --offline`).
- Depends on: Step 2.

## Changelog

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
