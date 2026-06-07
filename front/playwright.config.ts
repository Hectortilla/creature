import { defineConfig } from "@playwright/test";

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
 * Step 1 wires the frontend preview only; the backend `webServer` entry and the
 * data-seeding `globalSetup` arrive in Step 3.
 */
export default defineConfig({
	testDir: "./e2e",
	testMatch: "**/*.e2e.ts",
	forbidOnly: !!process.env.CI,
	retries: process.env.CI ? 2 : 0,
	reporter: [["html", { open: "never" }], ["list"]],
	use: {
		baseURL: "http://localhost:4173",
		trace: "on-first-retry",
	},
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
	webServer: {
		// Production build → `vite preview` on :4173 (frontend only for now).
		command: "npm run build && npm run preview",
		url: "http://localhost:4173",
		reuseExistingServer: !process.env.CI,
		// First boot runs a full production build — give it room.
		timeout: 180_000,
		// PUBLIC_API_URL is inlined at BUILD time (`$env/static/public`, see
		// src/lib/api.ts), so it must be set before `npm run build`. Setting it
		// here keeps the harness self-sufficient where no front/.env exists (CI).
		env: {
			PUBLIC_API_URL: process.env.PUBLIC_API_URL ?? "http://localhost:8000",
		},
	},
});
