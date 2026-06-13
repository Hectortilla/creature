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

- **`game.e2e` has no Linux screenshot baseline.** Only
  `front/e2e/game.e2e.ts-snapshots/board-chromium-darwin.png` is committed; the
  `toHaveScreenshot` at `front/e2e/game.e2e.ts:40` has no `*-linux.png`. On Linux
  CI that comparison currently fails (masked by `continue-on-error`). Promoting
  `game.e2e` to `@gating` without a Linux baseline would block every PR — so the
  baseline is a hard prerequisite (Step 1).
- **You can't generate a `-linux.png` on macOS** — Playwright suffixes baselines
  by platform, so a Mac run only ever writes `-darwin.png`. Step 1 must run on
  Linux (Docker or CI).
- **Tag form.** The 6 gameplay specs carry the tag inside the `describe` *title*
  (e.g. `test.describe("@nongating game start + board render", …)`), whereas
  `auth.e2e.ts` uses the option form `{ tag: "@gating" }`. `--grep` matches both.

## Steps

### Step 1 — Commit the Linux `game.e2e` screenshot baseline
- [ ] **Status:** not started
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
- [ ] **Status:** not started
- **First, confirm the green streak (§2).** If unmet, bail and report — do not
  proceed.
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

## Notes / decisions

- **Why gated, not flipped now:** the specs are historically flaky under load
  (WebGL/two-browser timing); the ratchet protects unrelated PRs from that flake
  until a real green streak proves it's settled. The loop running `make verify`
  every iteration (now report-only on `@nongating`) is what *produces* the streak
  evidence this plan consumes.
- **One tag, one flip:** because `make verify` mirrors CI, flipping the tag moves
  a spec into the hard gate in **both** places simultaneously — there is no
  separate "promote in the loop" step.
