import { defineConfig } from "@playwright/test";

import {
	E2E_API_URL,
	E2E_DATABASE_URL,
	E2E_GAME_SEED,
	E2E_REDIS_URL,
} from "./e2e/config";

/**
 * Playwright E2E harness for the running app.
 * Plan: docs/exec-plans/active/e2e-verification-harness.md
 *
 * Specs live under `e2e/` and are named `*.e2e.ts` so they never collide with
 * Vitest's `*.test.ts` / `*.spec.ts` units (vitest.config.ts excludes `e2e/**`).
 *
 * The app under test is the *production build* served by `vite preview` (:4173)
 * — the same artifact the `build` sensor produces, so it is closest to reality.
 * Chromium runs with SwiftShader software rendering so BabylonJS gets a WebGL2
 * context with no GPU present (needed for headless CI; see plan §5.6).
 *
 * DB isolation (plan §5.8 / Step 3.5): the backend runs on a DEDICATED port
 * bound to a DISPOSABLE `creature_e2e` DB (+ Redis logical DB 1), with
 * `reuseExistingServer: false` so a dev backend on :8000/creature can never be
 * silently reused. global-setup resets+migrates that DB each run; the dev DB is
 * never touched.
 *
 * Local prerequisite (Steps 3+): Postgres + Redis *running* — `make up`. The
 * harness now owns creating + migrating `creature_e2e` itself, so no manual
 * `alembic upgrade head` is needed for the e2e run.
 */
export default defineConfig({
	testDir: "./e2e",
	testMatch: "**/*.e2e.ts",
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 2 : 0,
	// Run specs serially. The gameplay/board specs share ONE backend process,
	// ONE preview server, and ONE pair of seeded users; running spec files in
	// parallel workers makes their guests race to join each other's freshly
	// created rooms (greedy "first joinable room" selection), which surfaces as
	// a backend "Failed to join room" when a room fills/starts mid-join. One
	// worker isolates each spec's room lifecycle — matching the reliable
	// single-spec behaviour.
	workers: 1,
	reporter: [["html", { open: "never" }], ["list"]],
	use: {
		baseURL: "http://localhost:4173",
		trace: "on-first-retry",
	},
	globalSetup: "./e2e/global-setup.ts",
	globalTeardown: "./e2e/global-teardown.ts",
	projects: [
		{
			name: "chromium",
			use: {
				browserName: "chromium",
				launchOptions: {
					// Software WebGL2 so BabylonJS renders without a GPU (plan §5.6).
					args: [
						"--use-gl=angle",
						"--use-angle=swiftshader",
						"--enable-unsafe-swiftshader",
					],
				},
			},
		},
	],
	webServer: [
		{
			// Backend: uvicorn on a DEDICATED port (8001), bound to the disposable
			// creature_e2e DB + Redis logical DB 1 via `env`. `reuseExistingServer:
			// false` guarantees a stray dev backend on :8000 (bound to the dev DB)
			// is never silently reused, defeating isolation (plan §5.8 reuse gotcha).
			command: `cd ../back && uv run python -m uvicorn app.main:app --host 0.0.0.0 --port ${new URL(E2E_API_URL).port}`,
			url: E2E_API_URL,
			reuseExistingServer: false,
			timeout: 60_000,
			env: {
				DATABASE_URL: E2E_DATABASE_URL,
				REDIS_URL: E2E_REDIS_URL,
				// Fixed RNG seed → deterministic deal/dice for the gameplay specs.
				GAME_SEED: E2E_GAME_SEED,
			},
		},
		{
			// Production build → `vite preview` on :4173.
			// PUBLIC_API_URL is inlined at BUILD time (`$env/static/public`, see
			// src/lib/api.ts), so it must be set before `npm run build`. Point it at
			// the dedicated e2e backend so the built UI talks to creature_e2e, not
			// a dev backend. Self-sufficient where no front/.env exists (CI).
			command: "npm run build && npm run preview",
			url: "http://localhost:4173",
			reuseExistingServer: !process.env.CI,
			// First boot runs a full production build — give it room.
			timeout: 180_000,
			env: {
				PUBLIC_API_URL: E2E_API_URL,
				// Build-time flag enabling the `window.__creature` drive API (tree-shaken from prod builds).
				PUBLIC_E2E_HOOKS: "1",
			},
		},
	],
});
