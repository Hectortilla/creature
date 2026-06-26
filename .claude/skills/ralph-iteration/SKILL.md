---
name: ralph-iteration
description: >-
  Run one Ralph-style iteration against a checkbox execution plan under
  `docs/exec-plans/active/`: pick the most important unblocked step (or the one
  named), implement and verify only that step, tick its box and commit, then
  stop. Use whenever the user wants to advance, run, continue, pick up, iterate
  on, or "do a ralph loop/iteration" over such a plan one step at a time — e.g.
  "do the next step of the e2e plan", "run a ralph iteration on
  e2e-verification-harness.md", "continue the verification-harness plan", or "run
  step 3". Prefer it any time the work involves a plan file under
  `docs/exec-plans/`, even if the user never says "skill".
---

# Ralph iteration — execute one step of an execution plan

Execution plans live in `docs/exec-plans/active/` as a queue of checkbox steps
(see `docs/exec-plans/active/README.md` for the format). This skill runs **one
"Ralph-style" iteration**: do a single, well-chosen step,
keep the plan honest about what's left, then stop — so the plan can be driven
forward one iteration at a time, typically by a fresh, clean-context agent each
run. Treat the plan file plus the repo's guides as your entire context;
everything you need to act on a step should be in that step or reachable from it.

Why one step at a time: it keeps each unit of progress small, shippable, and
attributable (**one commit and one stacked PR per iteration**), and it lets the
*next* run pick up cleanly from the file's updated state. Each iteration stacks
its branch on the previous step's branch, so looping N times leaves a clean
**stack of N PRs** to review in the morning. Doing several steps at once defeats
that handoff — so resist the urge, even if the next step looks easy.

## Inputs

Parse the plan to run from the arguments / request:

- **Plan file** — a filename or path, resolved under `docs/exec-plans/active/`
  (e.g. `e2e-verification-harness.md` →
  `docs/exec-plans/active/e2e-verification-harness.md`). Accept a bare name with
  or without the `.md` extension.
- **Step (optional)** — a specific step to run (e.g. "step 3"). If absent, you
  choose the step yourself (see step 2).

If no plan is named, list the plans in `docs/exec-plans/active/` (ignore
`README.md`) and ask the user which one — don't guess.

## Procedure

1. **Read your context.** Read the plan file in full, then `AGENTS.md` and any
   scoped guide it points at (`back/AGENTS.md` / `front/AGENTS.md`); for branch /
   PR conventions see `CONTRIBUTING.md`. These are your spec and your rules. If
   the plan has its own "how to execute" section, follow it where it is more
   specific than this skill.

2. **Choose the step.**
   - If the user named a step, do that one.
   - Otherwise **don't just grab the first unchecked box** — pick the *most
     valuable step you can actually make progress on right now*. Take all the
     unchecked (`[ ]`) steps, keep only those whose `Depends on` are already done
     (`[x]`) — that's the unblocked set — and from those choose the one with the
     highest leverage: what unblocks the most downstream work, retires the
     biggest risk or unknown, or is foundational for the rest, *and* is genuinely
     feasible in a single pass with what's available. State in one line which
     step you chose and why.
   - For a strictly linear plan this just resolves to the next step; for a
     backlog with independent tracks it lets you do the most important doable
     thing first. If nothing is unblocked, stop and say what's blocking.

3. **Implement only that step.** Do exactly what its `Do` list specifies and
   nothing more. Follow the repo rules: never hand-edit generated files, match
   existing conventions, and leave the **done-gate green** before you consider
   the step finished. The iteration's authoritative gate is **`make verify`**
   (repo root): it runs both deterministic gates (`make check`) **and** the
   running-app Playwright suite every iteration, so the e2e sensor is no longer
   a judgment call. Auth (`@gating`) must pass; gameplay (`@nongating`) runs
   report-only. Prerequisite: services up (`make up`) and the sandbox off.
   - For *fast* feedback while iterating you may run just the side you touched —
     `cd back && make check`, or the frontend gate `cd front && npm run lint &&
     npm run test && npm run deps:check && npm run build` — but the step is not
     done until **`make verify`** is green.
   - (see `AGENTS.md §4` for the authoritative gates)
   - **Never tamper with the gate to make it pass.** Never delete, skip, or
     `xfail` a test; never weaken an assertion; never lower a threshold
     (`fail_under`, vitest `thresholds`); never regenerate a golden/snapshot,
     widen an import-linter contract, or set `continue-on-error` in order to make
     the gate pass. If a gate is red, fix the code — or stop and report. Making
     the gate green by editing the gate is a **failed iteration**. (Legitimate
     harness changes are made deliberately, as their own step, and merge only
     behind the `harness-change` label — see `docs/harness.md`.)

   Also run any `Verify` commands the step itself lists; they must pass. A
   failing report-only `@nongating` e2e leg does **not** block the iteration, but
   record it in the PR body / `Notes for next agent` — it's the signal the
   `@nongating → @gating` ratchet consumes (see `docs/harness.md`).

4. **If the step is under-specified, blocked, or wrong, stop and report** what's
   missing rather than guessing or forcing it. A step you cannot verify is a step
   you cannot mark done. (Reshaping the plan is expected — see step 6 — but bail
   rather than fabricate a result.)

5. **Mark your step complete — only once the gate (`make verify`) and `Verify` are green:**
   - tick the box: `[ ]` → `[x]`;
   - set or append the step's status line, using today's date:
     `✅ done — <YYYY-MM-DD> — <one-line summary> — branch <branch> — commit <sha> — PR <url>`
     (the recorded **branch** is what the next iteration stacks on — see step 7);
   - if the next agent needs to know something, add a one-line
     `Notes for next agent:` under that step.

6. **Keep the plan honest — update the other steps if you learned something.**
   Doing the work often surfaces new facts: a hidden dependency, a step that's
   now unnecessary, a missing prerequisite, a better ordering, an acceptance
   criterion that turned out wrong. When that happens, don't silently move on —
   **edit the plan's remaining steps to match reality**: add new steps, split or
   merge them, rewrite a `Do` / `Acceptance` / `Verify` / `Depends on`, reorder,
   or delete ones that no longer apply. Keep every change grounded in what *this*
   iteration actually revealed (don't rewrite the whole plan on a hunch), and
   record what you changed and why — a one-line note per change under your step's
   `Notes for next agent:` or a short `## Changelog` entry — so the next
   iteration can trust the file.

7. **Stack a branch, commit, submit a PR, and stop.** Every iteration produces
   **one new branch stacked on the previous step's branch** and **one PR** — so an
   overnight loop leaves a clean stack of PRs to review in the morning. Use
   **Graphite** (`gt`); the stack state lives in `.git`, so it persists across
   fresh-agent iterations. **Never commit straight to `main`.** Opening and
   refreshing these PRs each iteration is the *intended* behaviour of this loop —
   do it without pausing to confirm each submit; just never force-push over remote
   commits you don't recognize.

   1. **Pick the base branch to stack on, and check it out:**
      - If no earlier step in this plan has a recorded branch yet, base on trunk:
        `gt checkout main`.
      - Otherwise base on the branch of the **most-recently-completed step** (the
        current tip of the plan's stack), read from its status line:
        `gt checkout <that-branch>`. If your step's `Depends on` points at a
        *different* completed step, base on **that** one instead so the stack
        mirrors real dependencies; with multiple deps, pick the latest as the base
        (`gt move --onto <branch>` can re-parent later). If a branch isn't tracked
        by Graphite yet, `gt track` it first.
   2. **Create the stacked branch with one commit — its body becomes the PR
      description.** Stage the step's work **and** your plan edits (`git add -A`),
      then create the branch with `gt create`. On submit Graphite turns the commit
      **subject into the PR title** and the commit **body into the PR description**,
      so write both now by passing each paragraph as its own `-m`: first the
      Conventional-Commits subject `-m "<type>(<scope>): <summary> (<plan> step
      <N>)"`, then the PR body as two further `-m` paragraphs —
      `## What problem does this solve?` and `## How does this solve it?` (exact
      format and example under **PR description** below). `<plan-slug>` is the plan
      filename without `.md`, `<N>` the step number, `<keyword>` a short descriptor
      — e.g. branch `spec/e2e-gameplay-harness/step-3/api-seeding`. Conventional
      Commits (see `CONTRIBUTING.md §4`) — valid types
      `feat`/`fix`/`chore`/`docs`/`refactor`/`test`/`perf`; scope = the area
      touched.
   3. **Submit / refresh the stack of PRs:** `gt submit --stack --no-edit` —
      creates this branch's PR and keeps the bases + titles + descriptions of the
      whole stack correct. `--no-edit` keeps it non-interactive and tells Graphite
      to take the PR **title and description straight from the commit message**
      (step 7.2) instead of opening an editor — essential for an unattended loop,
      and what lands the two-section description on the PR. (One-time per machine,
      the loop needs `gt init` and `gt auth` done first; if `gt submit` reports
      it's not initialized/authed, do those once, then re-run.)
   4. **Record the branch + PR URL** in the step's status line (step 5) so the next
      iteration knows what to stack on.

   (If the user said they'll handle branches/commits/PRs, skip the `gt` steps but
   still update the plan file and note that the commit/PR is pending.)

   If you just completed the **last** unchecked step, move the plan file to
   `docs/exec-plans/completed/` as your final action (its own commit on the top
   branch — give it the same two-section body, then `gt submit --stack --no-edit`
   to refresh). Then **stop — do not start
   another step** — and report: which step you chose and why, what changed, the
   gate / `Verify` output, the **branch + PR URL**, any plan edits you made, and
   any `Notes for next agent`.

## PR description

Each iteration's PR is read by a human in the morning, fast — and a long
description just doesn't get read. Keep it **short and skimmable**; the one job is
to communicate the *intention* of the change. Exactly two sections, nothing else:

```
## What problem does this solve?
<1–2 plain sentences: what was missing, broken, or blocked before this step.>

## How does this solve it?
<1–2 sentences, or 2–3 short bullets: the approach taken — not a file-by-file diff.>
```

This text is the **commit body** (step 7.2); `gt submit --no-edit` publishes it
verbatim as the PR description. Because it lives in the commit, it stays attached
to the work even if `gt submit` is deferred or blocked — whenever the PR is
(re)opened, Graphite uses it. Rules:

- No preamble, no checklist, no changelog, no "as requested" filler.
- Explain the *why* and the *approach*, not every file you touched — the diff
  already shows that.
- A reviewer caveat, if truly needed, gets one line. That's the budget.

Full example (the whole `gt create` from step 7.2):

```
gt create spec/e2e-gameplay-harness/step-3/api-seeding \
  -m "test(e2e): seed game state over the API (e2e-gameplay-harness step 3)" \
  -m "## What problem does this solve?
E2E tests had no way to put the board in a known state, so gameplay flows
couldn't be exercised end to end." \
  -m "## How does this solve it?
Adds a test-only POST /seed endpoint that loads a fixture board, plus a Playwright
helper that calls it before each gameplay spec."
```

## What a plan should provide

This skill works on any plan whose steps carry a checkbox plus enough detail to
act on cold — ideally a `Goal`, a concrete `Do` list, `Acceptance` criteria,
`Verify` commands, and `Depends on` where order matters, with shared design
context elsewhere in the file for steps to reference. If a plan is thinner than
that, lean on steps 4 and 6: do what's unambiguous, surface what isn't, and leave
the plan a little clearer than you found it.
