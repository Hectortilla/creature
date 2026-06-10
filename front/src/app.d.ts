// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	// Build-time `define` literal boolean gating `window.__creature` (see vite.config.ts).
	const __CREATURE_E2E_HOOKS__: boolean;

	namespace App {
		// interface Error {}
		interface Locals {
			token: string | null;
		}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}
}

declare module "$env/static/public" {
	export const PUBLIC_API_URL: string;
}

export {};
