.PHONY: run run_render install lint format format-check typecheck arch test test-cov check

PORT ?= 8000

# ── Run ──────────────────────────────────────────────────────────────────────
run:
	uv run python -m uvicorn app.main:app --reload

run_render:
	uv run python -m uvicorn app.main:app --host 0.0.0.0 --port $(PORT)

# ── Harness: computational sensors. See AGENTS.md and ../docs/harness.md. ─────
install:
	uv sync

lint:
	uv run ruff check app tests

format:
	uv run ruff format app tests
	uv run ruff check --fix app tests

format-check:
	uv run ruff format --check app tests

typecheck:
	uv run mypy app

arch:
	uv run lint-imports

test:
	uv run pytest -m "not integration"

test-cov:
	uv run pytest -m "not integration" --cov=app --cov-report=term-missing

# The deterministic "done" gate: lint + format + types + boundaries + tests
# (with the coverage floor; see [tool.coverage.report] fail_under).
check: lint format-check typecheck arch test-cov