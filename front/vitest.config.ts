import { fileURLToPath } from "node:url";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vitest/config";

/**
 * Standalone Vitest config for fast TS/Svelte unit tests.
 *
 * We deliberately do NOT load the full `sveltekit()` Vite plugin here: it pulls
 * in the BabylonJS `optimizeDeps`/static-copy machinery that has no place in a
 * unit run. Instead we register the lightweight `svelte()` compiler plugin (so
 * `.svelte` / `.svelte.ts` files can be tested) and wire up the `$lib` alias by
 * hand to mirror SvelteKit's resolution.
 *
 * Conventions:
 *  - Test files live next to the code they cover as `*.test.ts` / `*.spec.ts`,
 *    or under `src/**` generally.
 *  - Pure units (utils, stores, plain TS) are the target. Do NOT unit-test
 *    BabylonJS / 3D code here — drive that through the running app instead.
 */
export default defineConfig({
	plugins: [svelte({ hot: false })],
	resolve: {
		alias: {
			$lib: fileURLToPath(new URL("./src/lib", import.meta.url)),
		},
	},
	test: {
		// jsdom so component / DOM-touching units (e.g. changeThemeTo) can run.
		environment: "jsdom",
		include: ["src/**/*.{test,spec}.{js,ts}"],
		// `e2e/**` holds Playwright specs (`*.e2e.ts`) driven by playwright.config.ts,
		// not Vitest — exclude it so the two runners never fight over spec files.
		// The Babylon editor's 3D toolchain has its own runtime; only its pure-logic
		// dirs (`state/`, `game/`) are unit-testable here, so collect those and skip
		// the rest of `scripts/`.
		exclude: [
			"**/node_modules/**",
			"e2e/**",
			"src/babylon-editor/src/scripts/!(state|game)/**",
		],
		globals: true,
		coverage: {
			provider: "v8",
			reporter: ["text", "html"],
			// Measure our own first-party source + the pure game-client logic.
			include: ["src/lib/**", "src/babylon-editor/src/scripts/state/**"],
			exclude: [
				"src/lib/api/**", // generated OpenAPI client
				"src/lib/utils/generated/**", // generated action metadata
				"**/*.svelte", // component coverage is out of scope for now
				"**/*.d.ts",
			],
			// Glob-keyed floors so the unit-tested game-client logic must stay
			// covered; the rest of src/lib is left ungated (no top-level threshold).
			thresholds: {
				"src/babylon-editor/src/scripts/state/ActionBuilder.ts": {
					statements: 95,
					branches: 90,
					functions: 90,
					lines: 95,
				},
				"src/babylon-editor/src/scripts/state/GameStateStore.ts": {
					statements: 95,
					branches: 85,
					functions: 90,
					lines: 95,
				},
			},
		},
	},
});
