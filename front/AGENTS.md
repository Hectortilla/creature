# AGENTS.md — Working in `front/` (SvelteKit web client)

Scoped guide for the **frontend**. The canonical, cross-tool guide lives at the
repo root: [`../AGENTS.md`](../AGENTS.md) — read it first for the big picture,
the backend, and the OpenAPI/WebSocket contract. This file covers only `front/`.

Stack: **SvelteKit 2 · Svelte 5 (runes) · TypeScript · Vite 7 · BabylonJS**.
Package manager: **npm**. All commands below are run from `front/`.

## Install / run / build

```bash
npm install        # install deps (also runs `svelte-kit sync`)
npm run dev        # Vite dev server (http://localhost:5173)
npm run build      # production build
npm run preview    # serve the production build locally
```

The dev client talks to the backend at `PUBLIC_API_URL` (default
`http://localhost:8000`). Start the backend separately — see `../AGENTS.md §3`.

## Command table

| Command                             | What it does                                          |
| ----------------------------------- | ----------------------------------------------------- |
| `npm run dev`                       | Vite dev server with HMR                              |
| `npm run build`                     | Production build (`vite build`)                       |
| `npm run preview`                   | Serve the built app                                   |
| `npm run check`                     | `svelte-kit sync` + `svelte-check` (type/diagnostics) |
| `npm run check:watch`               | `svelte-check` in watch mode                          |
| `npm run format`                    | `prettier --write .` (fix formatting)                 |
| `npm run lint`                      | `prettier --check .` + `eslint .`                     |
| `npm run test`                      | `vitest run` (unit tests, one-shot)                   |
| `npm run test:watch`                | `vitest` (watch mode)                                 |
| `npm run test:cov`                  | `vitest run --coverage` (v8 coverage, text + HTML)    |
| `npm run deps:check`                | `depcruise` — module-boundary sensor (see below)      |
| `npm run generate`                  | regenerate the API client **and** action metadata     |
| `npm run generate-client`           | regenerate only the OpenAPI client                    |
| `npm run generate-action-metadata`  | regenerate only `utils/generated/*`                   |
| `npm run scene:generate`            | rebuild the BabylonJS scene assets                    |
| `npm run test:e2e`                  | Playwright running-app smoke (full stack, both flows) |
| `npm run test:e2e:gating`           | only `@gating` specs (the CI blocking subset)         |
| `npm run test:e2e:ui`               | Playwright UI mode (local debugging)                  |
| `npm run test:e2e:headed`           | headed run (local debugging)                          |
| `npm run test:e2e:update-snapshots` | regenerate the 3D screenshot baseline                 |

## Svelte 5 runes conventions

This codebase uses **Svelte 5 runes** — do not introduce legacy Svelte 4 idioms.

- Component props: `let { foo, bar }: Props = $props();` (not `export let`).
- Local reactive state: `let count = $state(0);`.
- Derived values: `const doubled = $derived(count * 2);`.
- Side effects: `$effect(() => { ... });` (avoid `$:` reactive statements).
- Cross-component reactive state lives in **rune-based stores** under
  `src/lib/stores/` as `*.svelte.ts` files (e.g. `auth.svelte.ts`,
  `card.svelte.ts`) that export a factory returning getters + actions.
- The Babylon→Svelte HUD bridge uses classic `svelte/store` writables under
  `src/lib/stores/babylon/` (consumed in markup via `$store` auto-subscription).
- Prefer TypeScript everywhere; keep BabylonJS/3D code inside
  `src/lib/components/babylon/` and the `src/babylon-editor/` sub-project.

## Generated-code contract (READ THIS)

Two trees are **auto-generated and must never be hand-edited**:

- `src/lib/api/*.gen.ts` + `src/lib/api/client/**` + `src/lib/api/core/**`
  — the OpenAPI client, generated from the backend's `openapi.json`.
- `src/lib/utils/generated/**` — action field metadata, derived from the
  generated types.

To change them, **change the backend** (the API schema / action definitions),
then regenerate:

```bash
npm run generate     # client + action metadata
```

Editing generated files by hand will be overwritten on the next `generate` and
is flagged in review. The hand-written API layer is `src/lib/api.ts` (configures
the client, adds auth interceptors, exposes `loginApi`/`registerApi`/`getMeApi`)
and the `src/lib/api/index.ts` barrel.

## `src/lib` structure & module-boundary rules

Real layout under `src/lib/`:

| Dir / file                                                                                   | Role                                                             |
| -------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| `api.ts`, `api/index.ts`                                                                     | hand-written API **facade** (re-exports + client config)         |
| `api/*.gen.ts`, `api/client/`, `api/core/`                                                   | **generated** OpenAPI client (do not edit)                       |
| `stores/`, `stores/babylon/`                                                                 | reactive state (runes + Babylon HUD writables)                   |
| `components/` (+ `cards/`, `input/`, `menu/`, `buttons/`, `creature/`, `babylon/`, `lobby/`) | Svelte UI components                                             |
| `utils/` (+ `utils/generated/`)                                                              | pure helpers; generated metadata                                 |
| `actions/`                                                                                   | Svelte `use:` actions (e.g. `parallax`)                          |
| `server/`                                                                                    | server-only helpers (`$lib/server`, never shipped to the client) |
| `types.ts`, `constants.ts`                                                                   | shared type aliases + constants                                  |
| `assets/`, `styles/`                                                                         | fonts/icons/logos; SCSS + rarity CSS                             |

The boundaries below are enforced by **`npm run deps:check`** (dependency-cruiser,
config in `.dependency-cruiser.cjs`). Layering, with imports pointing rightward:

```
components ─▶ stores ─▶ api (facade) ─▶ api/*.gen (generated client)
     │           │
     └───────────┴─▶ utils · constants · types        (leaf modules)
```

Enforced rules (all **error** severity unless noted):

1. **`no-direct-generated-client`** — only the API layer (`api.ts` + `api/**`)
   may import the generated client runtime (`client.gen` / `sdk.gen` / `client/`
   / `core/`). Everything else goes through the `$lib/api` facade.
2. **`stores-not-to-components`** — stores must not import components
   (direction is components → stores).
3. **`utils-are-leaves`** — `utils/` may use types, constants, generated
   metadata and other utils, but never stores, components, or the api facade.
4. **`no-circular`** — no circular dependencies (the generated client's own
   internal cycle is exempt — it is vendor output, not ours).
5. **`no-orphans`** (**warning**, optional) — flags dead first-party TS/JS
   units. `.svelte` files, SvelteKit convention files (routes/, `hooks.*`,
   `params/`), and `use:` actions are excluded because their imports cannot be
   reliably traced from markup.

**Documented exception:** `api.ts` imports `stores/auth.svelte` so the fetch
error-interceptor can clear auth on a 401. That single facade→store edge is
intentional; the rest of the api layer stays store-free.

Notes on the config: `$lib` is resolved via `tsconfig.depcruise.json` (a small
self-contained tsconfig — SvelteKit's generated one uses `baseUrl: null`, which
the cruiser cannot follow). The two Babylon HUD overlays that use Svelte store
auto-subscription (`$elementPools` / `$hoveredCard`) are excluded from cruising
due to a parser limitation in dependency-cruiser; see the comments in
`.dependency-cruiser.cjs`.

## Testing conventions

- Test runner is **Vitest** (`vitest.config.ts`, `jsdom` environment).
- Co-locate tests as `*.test.ts` / `*.spec.ts` next to the code under test
  (e.g. `src/lib/utils/formatHandle.test.ts`).
- Target **pure units** — utils, stores, plain TS. **Do not unit-test
  BabylonJS / 3D code**; exercise that through the running app instead — that
  mechanism now exists: the **Playwright E2E harness** (`npm run test:e2e`,
  specs under `e2e/*.e2e.ts`, config in `playwright.config.ts`) boots the full
  stack and drives a real browser through login → lobby and a two-browser
  game-start with the 3D board rendering. See
  [`../docs/harness.md`](../docs/harness.md) (running-app sensor) and the design
  in [`../docs/exec-plans/completed/e2e-verification-harness.md`](../docs/exec-plans/completed/e2e-verification-harness.md).
- For DOM/component tests, `@testing-library/svelte` + `jsdom` are available.
- See the exemplars `src/lib/utils/formatHandle.test.ts` and
  `src/lib/utils/getStrenghtsAndWeaknesses.test.ts` for the pattern.

## Definition of done

These **must be green** for a frontend change:

```bash
npm run lint        # prettier + eslint (ratcheted; gates on errors)
npm run test        # vitest
npm run deps:check  # module boundaries
npm run build       # production build
```

`npm run lint` (prettier + ratcheted eslint) **gates**: high-volume legacy eslint
rules are warnings, so it blocks new _errors_. Don't add new violations, and run
`npm run format` to fix formatting in your own files. `npm run check` (svelte-check)
still carries **pre-existing type debt** (incl. `babylon-editor/src`), so it runs in
CI non-blocking for now — don't add new type errors. Clearing it is a tracked rung
in [`../docs/harness.md`](../docs/harness.md).

If you touched a core flow (auth, lobby, game-start, or the 3D board), also run
the **running-app** harness — `npm run test:e2e` (full stack up; see
`../AGENTS.md §3`). Its CI `e2e` job gates only the auth flow (`@gating`); the
game-start + 3D flow is `@nongating` for now. This is the only sensor that
exercises the app actually running in a browser.

Don't bypass a sensor — fix the design. If a sensor itself is wrong, that's a
harness bug: fix the sensor (and note it here / in the root guide).
