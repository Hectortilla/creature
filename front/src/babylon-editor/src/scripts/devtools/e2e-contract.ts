/**
 * e2e-contract.ts — single source of truth for the `window.__creature` E2E API.
 *
 * Both halves of the e2e harness import it:
 *   - the in-page implementation (./E2EHarness.ts) — assigning
 *     `window.__creature` type-checks the implementation against this contract;
 *   - the Playwright side (front/e2e/harness.ts) — re-exports these types
 *     (type-only, erased at runtime) so specs and the in-page API can't drift.
 *
 * Everything is expressed in SERIALIZABLE terms (plain strings / numbers /
 * arrays, no Babylon or store classes) because every value crossing
 * `page.evaluate` must survive structured-clone anyway. KEEP THIS FILE
 * IMPORT-FREE: a runtime import would be loaded into the Playwright Node
 * process via front/e2e/harness.ts, and Babylon does not load under Node.
 *
 * Field shapes mirror the generated backend types (`GameCard`,
 * `AttackDefinition`, `ElementContribution` in $lib/api/types.gen.ts) — keep
 * optionality in sync with them, not with observed payloads.
 */

/** An element cost / contribution entry (`{element_id, amount}`). */
export interface ElementAmount {
	element_id: number;
	amount: number;
}

/** A card's attack, with its element cost (subset of `AttackDefinition`). */
export interface HarnessAttack {
	attack_id: number;
	name: string;
	damage: number;
	dice_rolls?: number | null;
	necessary_force?: ElementAmount[];
}

/** The slice of a card that specs assert on (subset of `GameCard`). */
export interface HarnessCard {
	instance_id: string;
	card_id: number;
	zone?: string;
	/** Runtime health (combat assertions). */
	current_health: number;
	health: number;
	/** Elements this card contributes while active (attack affordability). */
	element_contribution?: ElementAmount[];
	attacks?: HarnessAttack[];
}

/**
 * A valid action as served by the backend: an open record discriminated by
 * `action`, with the per-action target fields specs match on declared for
 * ergonomics. The index signature keeps it mutually assignable with the
 * in-page `ValidAction` (same open-record shape).
 */
export interface HarnessAction {
	action: string;
	player_id: string;
	/** play_card carries the target(s) as a list, not a scalar instance_id. */
	instance_ids?: string[];
	/** promote target. */
	instance_id?: string;
	/** swap pair. */
	supporting_card_id?: string;
	attacking_card_id?: string;
	/** attack. */
	attacker_id?: string;
	target_card_id?: string;
	[key: string]: unknown;
}

/** Which player's cards to read in `cardsInZone` — defaults to mine. */
export type HarnessPerspective = 'my' | 'opp';

/**
 * What a `waitForState` predicate may read. The in-page implementation passes
 * the live GameStateStore, which structurally satisfies this narrow view —
 * specs must only rely on what is declared here.
 */
export interface HarnessStore {
	getMyCardsInZone(zone: string): HarnessCard[];
	getOpponentCardsInZone(zone: string): HarnessCard[];
}

/**
 * The `window.__creature` test API. A thin read + drive facade over the game
 * singletons: reads come straight off GameStateStore; drive methods take the
 * REAL production path (ActionBuilder → GameConnection, server-validated);
 * waits resolve off the BoardController event bus (no sleeps). Attached only
 * in `PUBLIC_E2E_HOOKS` builds (tree-shaken otherwise).
 */
export interface CreatureHarness {
	// ── Read (straight off GameStateStore) ──────────────────────────────
	/** Opaque state snapshot — assert via the typed accessors below instead. */
	getState(): unknown;
	validActions(): HarnessAction[];
	phase(): string | null;
	isMyTurn(): boolean;
	myPlayerId(): string;
	opponentId(): string | null;
	cardsInZone(zone: string, perspective?: HarnessPerspective): HarnessCard[];

	// ── Project (real-pointer fidelity smoke) ────────────────────────────
	/** Page coords of a card mesh's centre, for `page.mouse.click(x, y)`. */
	screenPositionOf(instanceId: string): { x: number; y: number };
	/**
	 * Instance id the renderer's `scene.pick` resolves to at the given PAGE
	 * coords (or null) — confirms which overlapping card a click would select.
	 */
	cardAtScreenPoint(x: number, y: number): string | null;

	// ── Drive (real path: ActionBuilder.execute → GameConnection) ────────
	dispatch(action: HarnessAction): void;
	playCard(instanceId: string): HarnessAction;
	pass(): HarnessAction;
	swap(supportingId: string, attackingId: string): HarnessAction;
	attack(attackerId: string, targetId?: string): HarnessAction;
	promote(instanceId: string): HarnessAction;

	// ── Wait (off the BoardController event bus — no sleeps) ─────────────
	/** Resolves with the (opaque) state snapshot once `predicate` holds. */
	waitForState(predicate: (store: HarnessStore) => boolean, timeout?: number): Promise<unknown>;
	/** Resolves with the next `name` event's payload (opaque to specs). */
	nextEvent(name: string, timeout?: number): Promise<unknown>;
}

declare global {
	interface Window {
		__creature?: CreatureHarness;
	}
}
