import type { HudStoreSetter } from '$lib/stores/babylon/createHudStore';

/**
 * Base class for HUD bridges between Babylon-side state and a Svelte store.
 *
 * Owns the setter handshake (cache the latest payload, push on emit, replay
 * the cache when a late setter arrives) so subclasses focus on their own
 * data wiring — event subscriptions (event-driven bridges) or a per-frame
 * `update()` method called by HudController (polling bridges).
 */
export abstract class HudBridge<TPayload> {
	protected _setter: HudStoreSetter<TPayload> | null = null;
	protected _latest: TPayload | null = null;

	setSetter(fn: HudStoreSetter<TPayload>): void {
		this._setter = fn;
		if (this._latest !== null) fn(this._latest);
	}

	protected _emit(payload: TPayload | null): void {
		this._latest = payload;
		this._setter?.(payload);
	}

	dispose(): void {
		this._setter?.(null);
		this._setter = null;
		this._latest = null;
	}
}
