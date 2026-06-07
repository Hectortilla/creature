---
name: ralph-iteration
description: >-
  Run one Ralph-style iteration against an execution plan under
  `docs/exec-plans/active/`: do a single step, then stop. Use this whenever the
  user wants to advance, run, continue, pick up, iterate on, or "do a ralph
  loop/iteration" over one of these checkbox plans one step at a time — e.g. "do
  the next step of the e2e plan", "run a ralph iteration on
  e2e-verification-harness.md", "continue the verification-harness plan", "knock
  out the next item in <plan>.md", "run step 3 of <plan>", or when handing a plan
  step to a fresh/clean-context agent. Given a plan filename (and optional step
  number): it reads the plan; if no step is named it picks the MOST IMPORTANT
  step that is actually unblocked and doable now (not just the first box);
  implements ONLY that step; verifies it against the repo's done-gate; marks it
  complete (ticks the box, adds a status line, commits); and — if what it learned
  changes the remaining work — also updates the plan's other steps (adds, edits,
  reorders, or removes them) before stopping. Prefer this skill any time the work
  involves a plan file under `docs/exec-plans/`, even if the user never says the
  word "skill".
---

# Ralph iteration — execute one step of an execution plan

Execution plans live in `docs/exec-plans/active/` as a queue of checkbox steps.
This skill runs **one "Ralph-style" iteration**: do a single, well-chosen step,
keep the plan honest about what's left, then stop — so the plan can be driven
forward one iteration at a time, typically by a fresh, clean-context agent each
run. Treat the plan file plus the repo's guides as your entire context;
everything you need to act on a step should be in that step or reachable from it.

Why one step at a time: it keeps each unit of progress small, shippable, and
attributable (one commit per iteration), and it lets the *next* run pick up
cleanly from the file's updated state. Doing several steps at once defeats that
handoff — so resist the urge, even if the next step looks easy.

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
   scoped guide it points at (`back/AGENTS.md` / `front/AGENTS.md`). These are
   your spec and your rules. If the plan has its own "how to execute" section,
   follow it where it is more specific than this skill.

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
   existing conventions, and leave the relevant **done-gate green** before you
   consider the step finished:
   - backend changes → `cd back && make check`
   - frontend changes → `cd front && npm run lint && npm run test && npm run deps:check && npm run build`
   - (see `AGENTS.md §4` for the authoritative gates)

   Also run any `Verify` commands the step itself lists; they must pass.

4. **If the step is under-specified, blocked, or wrong, stop and report** what's
   missing rather than guessing or forcing it. A step you cannot verify is a step
   you cannot mark done. (Reshaping the plan is expected — see step 6 — but bail
   rather than fabricate a result.)

5. **Mark your step complete — only once the gate and `Verify` are green:**
   - tick the box: `[ ]` → `[x]`;
   - set or append the step's status line, using today's date:
     `✅ done — <YYYY-MM-DD> — <one-line summary> — commit <sha>`;
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

7. **Commit and stop.** Commit the step's work **and** any plan edits together,
   on a feature branch (branch off `main` first if you're on it — never commit
   straight to `main`), conventional-commit style, **one commit for this
   iteration**, e.g. `feat(scope): <step summary> (<plan> step <N>)`. (If the
   user said they will handle commits, skip committing but still update the file
   and note that the commit is pending.) If you just completed the **last**
   unchecked step, move the plan file to `docs/exec-plans/completed/` as your
   final action. Then **stop — do not start another step** — and report: which
   step you chose and why, what changed, the gate / `Verify` output, any plan
   edits you made, and any `Notes for next agent`.

## What a plan should provide

This skill works on any plan whose steps carry a checkbox plus enough detail to
act on cold — ideally a `Goal`, a concrete `Do` list, `Acceptance` criteria,
`Verify` commands, and `Depends on` where order matters, with shared design
context elsewhere in the file for steps to reference. If a plan is thinner than
that, lean on steps 4 and 6: do what's unambiguous, surface what isn't, and leave
the plan a little clearer than you found it.
