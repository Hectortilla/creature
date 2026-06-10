import { type Page } from "@playwright/test";

import { SCENE_TIMEOUT } from "./game-setup";

/**
 * Spec-side mirror of the build-gated `window.__creature` drive API (real impl in
 * E2EHarness.ts, Step 4 — outside this tsconfig, so specs re-declare only what they
 * touch). A thin facade over the production singletons: reads off GameStateStore,
 * drive methods take the REAL path (ActionBuilder → GameConnection), `waitForState`
 * resolves off the BoardController event bus (no sleeps).
 */

export interface HarnessCard {
	instance_id: string;
	card_id: number;
	zone: string;
	/** Runtime health (combat assertions, Step 6). */
	current_health?: number;
	health?: number;
}

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
}

export interface HarnessStore {
	getMyCardsInZone(zone: string): HarnessCard[];
	getOpponentCardsInZone(zone: string): HarnessCard[];
}

export interface CreatureHarness {
	isMyTurn(): boolean;
	phase(): string | null;
	myPlayerId(): string;
	opponentId(): string | null;
	validActions(): HarnessAction[];
	cardsInZone(zone: string, perspective?: "my" | "opp"): HarnessCard[];
	playCard(instanceId: string): HarnessAction;
	pass(): HarnessAction;
	swap(supportingId: string, attackingId: string): HarnessAction;
	attack(attackerId: string, targetId?: string): HarnessAction;
	promote(instanceId: string): HarnessAction;
	waitForState(
		predicate: (store: HarnessStore) => boolean,
		timeout?: number,
	): Promise<unknown>;
	nextEvent(name: string, timeout?: number): Promise<unknown>;
}

declare global {
	interface Window {
		__creature?: CreatureHarness;
	}
}

/**
 * Block until the harness has attached and the first state snapshot is applied.
 * The harness attaches at board-ready, BEFORE the opening WS state arrives, so
 * `phase()` is briefly null — wait for it to populate.
 */
export async function waitForGameReady(page: Page): Promise<void> {
	await page.waitForFunction(() => window.__creature?.phase() != null, null, {
		timeout: SCENE_TIMEOUT,
	});
}

/**
 * Multi-turn board-building drivers shared by the swap/attack specs (Steps 6b/6c).
 * Everything drives the REAL path through `window.__creature` and awaits state
 * changes off the event bus (no sleeps); each is bounded so a stuck transition fails fast.
 */

/** Upper bound on `pass`es in any single turn (DRAW…ATTACK is 7 phases). */
const MAX_PHASE_STEPS = 12;

/** Drive `pass` until the active page's turn ends. Must be that player's turn on entry. */
export async function passWholeTurn(page: Page): Promise<void> {
	await page.evaluate(async (max) => {
		const c = window.__creature!;
		for (let i = 0; i < max && c.isMyTurn(); i++) {
			const before = c.phase();
			c.pass();
			await c.waitForState(() => !c.isMyTurn() || c.phase() !== before);
		}
		if (c.isMyTurn()) {
			throw new Error("passWholeTurn: turn never ended");
		}
	}, MAX_PHASE_STEPS);
}

/**
 * Drive `pass` until the active page reaches `target` phase, same turn. Throws if the
 * turn ends first (i.e. `target` was auto-skipped) — only ask for a phase the board enters.
 */
export async function passToPhase(page: Page, target: string): Promise<void> {
	await page.evaluate(
		async ({ target, max }) => {
			const c = window.__creature!;
			for (let i = 0; i < max && c.isMyTurn() && c.phase() !== target; i++) {
				const before = c.phase();
				c.pass();
				await c.waitForState(() => !c.isMyTurn() || c.phase() !== before);
			}
			if (c.phase() !== target || !c.isMyTurn()) {
				throw new Error(
					`passToPhase: never reached ${target} (phase=${c.phase()}, myTurn=${c.isMyTurn()})`,
				);
			}
		},
		{ target, max: MAX_PHASE_STEPS },
	);
}
