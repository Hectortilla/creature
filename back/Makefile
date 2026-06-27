.PHONY: run run_render install lint format format-check typecheck arch deadcode test test-cov check

PORT ?= 8000

# Harness verbosity: run a sensor quietly — one `✓` line on success, the full
# captured output (stdout+stderr) only on failure. Keeps green gates near-silent.
define quiet
@out=$$($(1) 2>&1); st=$$?; \
if [ $$st -ne 0 ]; then printf '%s\n' "$$out"; exit $$st; fi; echo "✓ $(2)"
endef

# ── Run ──────────────────────────────────────────────────────────────────────
run:
	uv run python -m uvicorn app.main:app --reload

run_render:
	uv run python -m uvicorn app.main:app --host 0.0.0.0 --port $(PORT)

# ── Harness: computational sensors. See AGENTS.md and ../docs/harness.md. ─────
install:
	uv sync

lint:
	$(call quiet,uv run ruff check app tests,lint)

format:
	uv run ruff format app tests
	uv run ruff check --fix app tests

format-check:
	$(call quiet,uv run ruff format --check app tests,format-check)

typecheck:
	$(call quiet,uv run mypy app,typecheck)

arch:
	$(call quiet,uv run lint-imports,arch)

deadcode:
	$(call quiet,uv run vulture,vulture)
	$(call quiet,uv run deptry .,deptry)

test:
	$(call quiet,uv run pytest -m "not integration",test)

test-cov:
	$(call quiet,uv run pytest -m "not integration" --cov=app --cov-report=term-missing,test-cov)

# The deterministic "done" gate: lint + format + types + boundaries + dead-code
# + tests (with the coverage floor; see [tool.coverage.report] fail_under).
check: lint format-check typecheck arch deadcode test-cov