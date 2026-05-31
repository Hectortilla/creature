/**
 * dependency-cruiser config — module-boundary sensor for the SvelteKit frontend.
 *
 * Run with: `npm run deps:check` (== `depcruise src --config .dependency-cruiser.cjs`).
 *
 * The boundaries below mirror the real `src/lib` layout (see front/AGENTS.md):
 *
 *   components ──▶ stores ──▶ api(facade) ──▶ api/*.gen (generated OpenAPI client)
 *        │            │
 *        └────────────┴──▶ utils, constants, types   (leaf modules)
 *
 * Documented exceptions (intentional, encoded as scoped rules — not failures):
 *   - `src/lib/api.ts` (the API facade) imports `src/lib/stores/auth.svelte` so
 *     the fetch error-interceptor can clear auth on 401. That single facade→store
 *     edge is allowed; the rest of the api layer stays store-free.
 *
 * Alias resolution: `$lib` is resolved via a dedicated tsconfig
 * (tsconfig.depcruise.json) that declares `baseUrl` + `paths` explicitly.
 * SvelteKit's generated .svelte-kit/tsconfig.json uses `baseUrl: null`, which
 * dependency-cruiser's resolver does not honour, so `$lib/...` imports would
 * otherwise look like unresolved externals and the boundary rules would see no
 * graph. `$app` / `$env` / `$service-worker` are SvelteKit virtual modules with
 * no file on disk, so they are excluded from the crawl entirely (they would
 * otherwise show up as bogus unresolved orphans).
 */

/** Path matching the generated OpenAPI client (must NEVER be hand-edited). */
const GENERATED_CLIENT = "^src/lib/api/(client\\.gen|sdk\\.gen|client/|core/)";

/** The hand-written API layer: src/lib/api.ts AND everything under src/lib/api/. */
const API_LAYER = "^src/lib/api(\\.ts$|/)";

/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
	forbidden: [
		{
			name: "no-circular",
			comment:
				"Circular dependencies make modules hard to test and reason about. Break the cycle (often by extracting a shared type/util). The generated OpenAPI client is exempt — its internal cycles (types.gen ↔ utils.gen) are the vendor tool's output, not ours to fix.",
			severity: "error",
			from: { pathNot: "^src/lib/api/(client/|core/)" },
			to: { circular: true },
		},
		{
			name: "no-direct-generated-client",
			comment:
				"Only the API layer (src/lib/api.ts + src/lib/api/**) may touch the generated OpenAPI client runtime (client.gen / sdk.gen / client/ / core/). Everything else must go through the $lib/api facade. Generated code is never hand-edited — change the backend and run `npm run generate`.",
			severity: "error",
			from: { pathNot: API_LAYER },
			to: { path: GENERATED_CLIENT },
		},
		{
			name: "stores-not-to-components",
			comment:
				"Layering is components → stores, never the reverse. Stores must not import Svelte components.",
			severity: "error",
			from: { path: "^src/lib/stores/" },
			to: { path: "^src/lib/components/" },
		},
		{
			name: "utils-are-leaves",
			comment:
				"utils/ are leaf modules: they may use types, constants, generated metadata and other utils, but must not depend on stores, components, or the api facade. Keeps them trivially unit-testable.",
			severity: "error",
			from: { path: "^src/lib/utils/" },
			to: {
				path: [
					"^src/lib/stores/",
					"^src/lib/components/",
					"^src/lib/api(\\.ts$|/index\\.ts$)",
				],
			},
		},
		{
			name: "no-orphans",
			comment:
				"Modules with no incoming/outgoing edges are usually dead code. Scoped to first-party TS/JS units (utils, stores, plain libs) where orphan detection is reliable, and reported as a WARNING (never a gate failure). Excluded categories are either generated, framework-loaded by convention, or consumed in ways dependency-cruiser cannot see from a .svelte file: " +
				"(1) .svelte components — their component-to-component and `use:`-action imports are not fully resolved by the bundled Svelte parser, so every component would be a false-positive orphan; " +
				"(2) SvelteKit convention entry points (routes/, hooks.*.ts, params/) loaded by the framework, not imported; " +
				"(3) Svelte actions (lib/actions/) used only via `use:` in markup; " +
				"(4) generated code, assets, styles, type-only barrels, and tests.",
			severity: "warn",
			from: {
				orphan: true,
				pathNot: [
					"\\.svelte$", // see (1)
					"^src/routes/", // see (2)
					"^src/hooks\\.", // see (2)
					"^src/params/", // see (2)
					"^src/lib/actions/", // see (3)
					"\\.(json|svg|woff2?|scss|css|d\\.ts)$",
					"^src/lib/api/", // generated client
					"^src/lib/utils/generated/", // generated metadata
					"^src/lib/(index|types|constants)\\.ts$",
					"^src/lib/assets/",
					"^src/lib/styles/",
					"(^|/)\\$types", // SvelteKit generated route types
					"\\.(test|spec)\\.(js|ts)$",
				],
			},
			to: {},
		},
	],
	options: {
		/** Resolve the `$lib` alias from a dedicated, self-contained tsconfig. */
		tsConfig: { fileName: "tsconfig.depcruise.json" },
		/** Follow type-only imports too (e.g. `import type { Foo } from '...'`). */
		tsPreCompilationDeps: true,
		/** Don't crawl into dependencies or the Babylon editor sub-project. */
		doNotFollow: { path: "node_modules" },
		exclude: {
			path: [
				"node_modules",
				"src/babylon-editor",
				"\\.svelte-kit/",
				// SvelteKit virtual modules — no file on disk, nothing to cruise.
				"^\\$(app|env|service-worker)(/|$)",
				// KNOWN LIMITATION: dependency-cruiser's bundled Svelte parser rejects
				// Svelte store auto-subscription (`$elementPools` / `$hoveredCard`) as
				// an "illegal variable name" and aborts the whole run. These two HUD
				// overlays are the only files that use that syntax; every other
				// component cruises fine. They are leaf consumers (component → store),
				// so skipping them does not weaken any boundary rule. Remove these
				// entries if the parser gains store-subscription support.
				"src/lib/components/babylon/ElementPoolsOverlay\\.svelte$",
				"src/lib/components/babylon/HoveredCardOverlay\\.svelte$",
			],
		},
		enhancedResolveOptions: {
			exportsFields: ["exports"],
			conditionNames: [
				"import",
				"require",
				"node",
				"default",
				"svelte",
				"browser",
			],
			extensions: [".js", ".ts", ".svelte", ".json"],
		},
	},
};
