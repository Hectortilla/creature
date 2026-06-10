.PHONY: up down check check-back check-front

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
	cd front && npm run check:e2e && npm run test && npm run deps:check && npm run build
	-cd front && npm run lint   # non-blocking: pre-existing debt (see docs/harness.md)
	-cd front && npm run check  # non-blocking: pre-existing debt
