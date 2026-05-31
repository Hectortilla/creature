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
