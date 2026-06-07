/**
 * Single source of truth for the E2E stack's endpoints (plan §5.8 / Step 3.5).
 *
 * The e2e backend runs on a DEDICATED port bound to a DISPOSABLE database, so it
 * can never be confused with — or silently reuse — a dev backend on :8000 bound
 * to the dev `creature` DB. `playwright.config.ts` wires these into the
 * `webServer` entries; `global-setup.ts` / `global-teardown.ts` use them to
 * create/reset/drop the throwaway DB and to talk to the backend.
 *
 * Overrides use E2E-specific env var names (never the ambient `DATABASE_URL` /
 * `REDIS_URL`) so a developer who exported those pointing at the *dev* stack
 * cannot accidentally make the harness reset their real database.
 */

/** Dedicated backend port — distinct from the dev backend's :8000. */
export const E2E_BACKEND_PORT = 8001;

/** Backend base URL the frontend build and the seeding script both target. */
export const E2E_API_URL =
	process.env.PUBLIC_API_URL ?? `http://localhost:${E2E_BACKEND_PORT}`;

/**
 * Disposable Postgres database for E2E — NEVER the dev `creature` DB. The name
 * must end in `_e2e`; `assertDisposableDb` (db.ts) enforces this before any
 * drop/create so a misconfiguration can't nuke a real database.
 */
export const E2E_DATABASE_URL =
	process.env.E2E_DATABASE_URL ??
	"postgresql://postgres:postgres@localhost:5432/creature_e2e";

/** Dedicated Redis logical DB (1) — isolates room/session state from dev (0). */
export const E2E_REDIS_URL =
	process.env.E2E_REDIS_URL ?? "redis://localhost:6379/1";
