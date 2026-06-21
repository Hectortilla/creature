.PHONY: up down check check-back check-front verify

# Local services (Postgres 14 + Redis) via Homebrew.
up:
	brew services start postgresql@14
	brew services start redis

down:
	brew services stop postgresql@14
	brew services stop redis

# Run both "done" gates. See AGENTS.md.
check: check-back check-front

check-back:
	$(MAKE) -C back check

check-front:
	cd front && npm run lint && npm run check:e2e && npm run test && npm run deps:check && npm run build
	-cd front && npm run check  # non-blocking: svelte-check type debt (see docs/harness.md)

# Autonomy / loop gate: `make check` + the running-app e2e suite. See AGENTS.md §4.
verify: check
	cd front && npm run test:e2e:gating -- --retries=2  # auth + 5 stable gameplay specs (blocking)
	-cd front && npm run test:e2e -- --grep @nongating --retries=2  # @nongating: pointer.e2e only, report-only
