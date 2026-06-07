# Execution plans — active

A lightweight plan for any multi-step change lives here while it's in flight, then
moves to [`../completed/`](../completed/) when done. This gives an agent a stable
place to record intent and progress so context survives across sessions.

**Convention**

- One Markdown file per effort, kebab-case (e.g. `add-spectator-mode.md`).
- Suggested sections: **Goal**, **Plan** (checklist), **Notes / decisions**,
  **Verification**.
- Re-read your plan at the start of each work session and tick items off as you go.
- When the work ships, move the file to `../completed/`.

**Running a plan step-by-step**

To execute a plan one step at a time with a fresh, clean-context agent each time
(a Ralph-style loop), use the spec-agnostic **`ralph-iteration`** skill (in
Claude Code: `/ralph-iteration <plan-filename>`). Give it a plan's filename and
it picks the most valuable unblocked step, implements that one step, verifies
against the gate, marks it done (and revises the remaining steps if it learns
something), then commits.
