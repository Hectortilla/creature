import { writable, type Writable } from 'svelte/store';

export type HudStoreSetter<T> = (payload: T | null) => void;

/**
 * Standard HUD-store shape: a nullable writable plus a typed setter helper.
 *
 * Used by every Babylon-to-Svelte HUD overlay (hovered card, element pools, …)
 * so each new bridge only declares its payload type.
 */
export function createHudStore<T>(): [Writable<T | null>, HudStoreSetter<T>] {
	const store: Writable<T | null> = writable(null);
	const set: HudStoreSetter<T> = (payload) => store.set(payload);
	return [store, set];
}
