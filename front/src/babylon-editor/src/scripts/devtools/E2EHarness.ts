/**
 * E2EHarness — build-gated `window.__creature` test API.
 *
 * A thin read + drive facade over the game singletons, attached to `window` only
 * when the build-time `PUBLIC_E2E_HOOKS` flag is set (wired from
 * BabylonEditorScene.svelte); unset builds tree-shake it away. It drives actions
 * through the REAL production path (ActionBuilder → GameConnection), so it's no
 * privilege escalation — the socket is authenticated and the server validates
 * every action. Specs read off GameStateStore and await transitions on the
 * BoardController event bus (no sleeps).
 */

import BoardController from '../BoardController';
import GameConnection from '../game/GameConnection';
import { GameStateStore } from '../state/GameStateStore';
import { ActionBuilder } from '../state/ActionBuilder';
import type { ValidAction } from '../game/types';
import type { ClientCard, ClientGameState, TurnPhase, Zone } from '../game/models';
import type { StateChangeEvents } from '../state/events';

/** Which player's cards to read in `cardsInZone` — defaults to mine. */
type Perspective = 'my' | 'opp';

/** Predicate evaluated against the live store in `waitForState`. */
type StatePredicate = (store: GameStateStore) => boolean;

/**
 * BoardController events signalling the store may have changed; `waitForState`
 * re-checks its predicate after each. The snapshot is applied to the store BEFORE
 * these fire, so the predicate always observes fresh state.
 */
const STATE_CHANGE_EVENTS: (keyof StateChangeEvents)[] = [
	'gameStarted',
	'cardMoved',
	'cardsSwapped',
	'phaseChanged',
	'turnChanged',
	'turnEnded',
	'cardHealthChanged',
	'cardDestroyed',
	'cardAssociated',
	'cardEvolved',
	'validActionsChanged',
	'gameOver',
	'actionFailed',
];

const DEFAULT_TIMEOUT_MS = 10_000;

export interface E2EHarness {
	// ── Read (straight off GameStateStore) ──────────────────────────────
	getState(): ClientGameState | null;
	validActions(): ValidAction[];
	phase(): TurnPhase | null;
	isMyTurn(): boolean;
	myPlayerId(): string;
	opponentId(): string | null;
	cardsInZone(zone: Zone, perspective?: Perspective): ClientCard[];

	// ── Drive (real path: ActionBuilder.execute → GameConnection) ────────
	dispatch(action: ValidAction): void;
	playCard(instanceId: string): ValidAction;
	pass(): ValidAction;
	swap(supportingId: string, attackingId: string): ValidAction;
	attack(attackerId: string, targetId?: string): ValidAction;
	promote(instanceId: string): ValidAction;

	// ── Wait (off the BoardController event bus — no sleeps) ─────────────
	waitForState(predicate: StatePredicate, timeout?: number): Promise<ClientGameState | null>;
	nextEvent<K extends keyof StateChangeEvents>(
		name: K,
		timeout?: number,
	): Promise<StateChangeEvents[K]>;
}

declare global {
	interface Window {
		__creature?: E2EHarness;
	}
}

// ── Singleton accessors (resolved lazily, at call time) ────────────────

function requireStore(): GameStateStore {
	const store = GameStateStore.instance;
	if (!store) throw new Error('E2EHarness: GameStateStore not initialized');
	return store;
}

function requireBoard(): BoardController {
	const board = BoardController.instance;
	if (!board) throw new Error('E2EHarness: BoardController not initialized');
	return board;
}

// Cache one ActionBuilder per live connection — a new game gets a fresh one.
let cachedBuilder: ActionBuilder | null = null;
let cachedBuilderConn: GameConnection | null = null;

function requireBuilder(): ActionBuilder {
	const conn = GameConnection.instance;
	if (!conn) throw new Error('E2EHarness: GameConnection not initialized');
	if (!cachedBuilder || cachedBuilderConn !== conn) {
		cachedBuilder = new ActionBuilder(conn);
		cachedBuilderConn = conn;
	}
	return cachedBuilder;
}

function findValidAction(match: (a: ValidAction) => boolean, describe: string): ValidAction {
	const action = requireStore().validActions.find(match);
	if (!action) {
		throw new Error(`E2EHarness: no valid action found for ${describe}`);
	}
	return action;
}

// ── Harness factory ────────────────────────────────────────────────────

export function attachE2EHarness(): E2EHarness {
	const dispatch = (action: ValidAction): void => {
		requireBuilder().execute(action);
	};

	const harness: E2EHarness = {
		// Read
		getState: () => requireStore().state,
		validActions: () => requireStore().validActions,
		phase: () => requireStore().currentPhase,
		isMyTurn: () => requireStore().isMyTurn,
		myPlayerId: () => requireStore().myPlayerId,
		opponentId: () => requireStore().getOpponentId(),
		cardsInZone: (zone, perspective = 'my') =>
			perspective === 'opp'
				? requireStore().getOpponentCardsInZone(zone)
				: requireStore().getMyCardsInZone(zone),

		// Drive
		dispatch,
		playCard: (instanceId) => {
			// play_card carries `instance_ids: [cid]` (a list), not a scalar `instance_id`.
			const action = findValidAction(
				(a) =>
					a.action === 'play_card' &&
					Array.isArray(a.instance_ids) &&
					(a.instance_ids as string[]).includes(instanceId),
				`play_card ${instanceId}`,
			);
			dispatch(action);
			return action;
		},
		pass: () => {
			const action = findValidAction((a) => a.action === 'pass', 'pass');
			dispatch(action);
			return action;
		},
		swap: (supportingId, attackingId) => {
			const action = findValidAction(
				(a) =>
					a.action === 'swap' &&
					a.supporting_card_id === supportingId &&
					a.attacking_card_id === attackingId,
				`swap ${supportingId} ↔ ${attackingId}`,
			);
			dispatch(action);
			return action;
		},
		attack: (attackerId, targetId) => {
			const action = findValidAction(
				(a) =>
					a.action === 'attack' &&
					a.attacker_id === attackerId &&
					(targetId === undefined ? !a.target_card_id : a.target_card_id === targetId),
				`attack ${attackerId} → ${targetId ?? '(no defender)'}`,
			);
			dispatch(action);
			return action;
		},
		promote: (instanceId) => {
			const action = findValidAction(
				(a) => a.action === 'promote' && a.instance_id === instanceId,
				`promote ${instanceId}`,
			);
			dispatch(action);
			return action;
		},

		// Wait
		waitForState: (predicate, timeout = DEFAULT_TIMEOUT_MS) =>
			new Promise<ClientGameState | null>((resolve, reject) => {
				const store = requireStore();
				if (predicate(store)) {
					resolve(store.state);
					return;
				}
				const board = requireBoard();
				const unsubscribe = (): void => {
					for (const event of STATE_CHANGE_EVENTS) {
						board.off(event, check as never);
					}
				};
				const timer = setTimeout(() => {
					unsubscribe();
					reject(new Error(`E2EHarness: waitForState timed out after ${timeout}ms`));
				}, timeout);
				function check(): void {
					if (!predicate(store)) return;
					clearTimeout(timer);
					unsubscribe();
					resolve(store.state);
				}
				for (const event of STATE_CHANGE_EVENTS) {
					board.on(event, check as never);
				}
			}),
		nextEvent: <K extends keyof StateChangeEvents>(name: K, timeout = DEFAULT_TIMEOUT_MS) =>
			new Promise<StateChangeEvents[K]>((resolve, reject) => {
				const board = requireBoard();
				const timer = setTimeout(() => {
					board.off(name, handler);
					reject(new Error(`E2EHarness: nextEvent("${String(name)}") timed out after ${timeout}ms`));
				}, timeout);
				function handler(data: StateChangeEvents[K]): void {
					clearTimeout(timer);
					board.off(name, handler);
					resolve(data);
				}
				board.on(name, handler);
			}),
	};

	window.__creature = harness;
	console.log('[E2EHarness] window.__creature attached');
	return harness;
}
