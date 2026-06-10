# Contributing to `creature`

Humans and AI agents both work in this repo. The conventions below keep changes
safe and reviewable. Start from [`AGENTS.md`](AGENTS.md) (the canonical guide);
this file covers the contribution *process*.

## 1. Setup

```bash
make up                              # Postgres 14 + Redis
cd back && make install              # uv sync
cd front && npm install
```

## 2. Make a change

- **Branch off `main`** — never commit directly to `main`. The team uses
  [Graphite](https://graphite.dev) for stacked PRs (`gt create`, `gt submit`); plain
  `git` + GitHub PRs are fine too.
- Keep PRs small and focused. For anything multi-step, drop a short plan in
  [`docs/exec-plans/active/`](docs/exec-plans/active/) first and move it to
  `completed/` when done.
- Follow the coding style in [`.claude/rules/`](.claude/rules/) (fail-fast; DRY).
- Never hand-edit generated files (`front/src/lib/api/*.gen.ts`,
  `front/src/lib/utils/generated/*`) — change the backend and run
  `cd front && npm run generate`.

## 3. Pass the gate before you push ("definition of done")

| Touched | Run |
| ------- | --- |
| `back/` | `cd back && make check` |
| `front/` | `cd front && npm run test && npm run deps:check && npm run build` |
| either | `make check` from the repo root runs both |

> `npm run lint` (prettier + eslint) and `npm run check` (svelte-check) carry
> pre-existing debt in app/legacy code, so they run as **non-blocking** CI steps for
> now — don't add new violations, and run `npm run format` on files you touch.
> Clearing the backlog is tracked in [`docs/harness.md`](docs/harness.md).

`make check` is the deterministic gate: ruff, ruff-format, mypy, import-linter,
and pytest for the backend. A change isn't done until it's green. Fast checks also
run automatically via [pre-commit](#5-pre-commit-hooks).

## 4. Commits & PRs

- **Conventional commits**: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`,
  `test:`, …
- PRs use [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md);
  fill in what changed, how you verified, and tick the gate checklist.
- **Required CI checks** (configure as branch-protection on `main`): the backend
  job, the frontend job, and the docs link-check in
  [`.github/workflows/ci.yml`](.github/workflows/ci.yml) / `docs.yml`.
- Reviews: the on-demand `/code-review` and `/security-review` Claude Code skills
  are available; an automated Claude PR review can be switched on by adding an
  `ANTHROPIC_API_KEY` secret (see `.github/workflows/claude-review.yml`).

## 5. Pre-commit hooks

```bash
pipx install pre-commit   # or: uv tool install pre-commit
pre-commit install        # from the repo root
```

Hooks run the fast subset (ruff lint+format, prettier, eslint, whitespace) on
changed files. Run on everything with `pre-commit run --all-files`.

## 6. Tests

- Backend unit tests: `back/tests/unit/` (marker `unit`, no DB) — use the
  `empty_state` / `place_card` fixtures in `back/tests/conftest.py`.
- Backend integration tests: `back/tests/integration/` (marker `integration`,
  needs Postgres via `db_session`) — excluded from `make test`, run in CI.
- Frontend: Vitest (`npm run test`); put unit tests next to the code or under
  `src/**/*.test.ts`.

## 7. Evolving the harness

The quality controls themselves are part of the codebase. If a class of bug or a
recurring misunderstanding slips through, **improve the control** — add a test,
lint rule, or boundary contract; or sharpen a guide — and note it in
[`docs/harness.md`](docs/harness.md). Don't just patch the instance.
