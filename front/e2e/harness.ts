import { type Page } from "@playwright/test";

import { SCENE_TIMEOUT } from "./game-setup";

/**
 * Spec-side mirror of the build-gated `window.__creature` drive API (real impl in
 * E2EHarness.ts, Step 4 — outside this tsconfig, so specs re-declare only what they
 * touch). A thin facade over the production singletons: reads off GameStateStore,
 * drive methods take the REAL path (ActionBuilder → GameConnection), `waitForState`
 * resolves off the BoardController event bus (no sleeps).
 */

/** An element cost / contribution entry (`{element_id, amount}`). */
export interface ElementAmount {
	element_id: number;
	amount: number;
}

export interface HarnessAttack {
	attack_id: number;
	name: string;
	damage: number;
	dice_rolls: number;
	necessary_force: ElementAmount[];
}

export interface HarnessCard {
	instance_id: string;
	card_id: number;
	zone: string;
	/** Runtime health (combat assertions, Steps 6/6c). */
	current_health?: number;
	health?: number;
	/** Elements this card contributes while active (Step 6c affordability). */
	element_contribution?: ElementAmount[];
	/** This card's attacks, with their element costs (Step 6c). */
	attacks?: HarnessAttack[];
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
	/** Page coords of a card mesh's centre, for `page.mouse.click` (Step 7). */
	screenPositionOf(instanceId: string): { x: number; y: number };
	/** Instance id the renderer's scene.pick resolves to at page coords (Step 7). */
	cardAtScreenPoint(x: number, y: number): string | null;
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

/**
 * In PLACEMENT, play `count` distinct hand cards into SUPPORTING (real path); resolve
 * to their instance ids in order. Caller must be on PLACEMENT with ≥ `count` playable cards.
 */
export async function placeIntoSupporting(
	page: Page,
	count: number,
): Promise<string[]> {
	return page.evaluate(async (n) => {
		const c = window.__creature!;
		const placed: string[] = [];
		for (let i = 0; i < n; i++) {
			await c.waitForState(() =>
				c
					.validActions()
					.some(
						(a) =>
							a.action === "play_card" &&
							!!a.instance_ids &&
							!placed.includes(a.instance_ids[0]),
					),
			);
			const action = c
				.validActions()
				.find(
					(a) =>
						a.action === "play_card" &&
						!!a.instance_ids &&
						!placed.includes(a.instance_ids[0]),
				);
			const id = action!.instance_ids![0];
			c.playCard(id);
			await c.waitForState((s) =>
				s
					.getMyCardsInZone("SUPPORTING")
					.some((card) => card.instance_id === id),
			);
			placed.push(id);
		}
		return placed;
	}, count);
}

/**
 * Promote a SUPPORTING card to ATTACKING: pass to PROMOTION, `promote` it (real path),
 * await the move. The card must be promotable (placed ≥1 full turn ago) — call on turn 2+.
 */
export async function promoteToAttacking(
	page: Page,
	instanceId: string,
): Promise<void> {
	await passToPhase(page, "PROMOTION");
	await page.evaluate(async (id) => {
		const c = window.__creature!;
		await c.waitForState(() =>
			c
				.validActions()
				.some((a) => a.action === "promote" && a.instance_id === id),
		);
		c.promote(id);
		await c.waitForState((s) =>
			s.getMyCardsInZone("ATTACKING").some((card) => card.instance_id === id),
		);
	}, instanceId);
}

/** Block on the active page until it becomes this player's turn again. */
export async function waitForMyTurn(page: Page): Promise<void> {
	await page.evaluate(() =>
		window.__creature!.waitForState(() => window.__creature!.isMyTurn()),
	);
}
