/**
 * GameStateStore — pure client-side game state container.
 *
 * Single source of truth for all game data.  Receives authoritative
 * server snapshots via `applyServerState` and exposes read-only queries.
 * Contains NO event bus — all typed events are emitted by BoardController.
 *
 * Pure TypeScript — no BabylonJS imports, no scene dependencies.
 */

import type {
	Zone,
	TurnPhase,
	ClientCard,
	ClientGameState,
	GameStateForPlayer,
	GameCard,
} from '../game/models';

import type { ValidAction } from '../game/types';

export class GameStateStore {
	static instance: GameStateStore | null = null;

	private _state: ClientGameState | null = null;
	private _myPlayerId = '';
	private _validActions: ValidAction[] = [];

	private constructor(myPlayerId: string) {
		this._myPlayerId = myPlayerId;
	}

	static getOrCreate(myPlayerId: string): GameStateStore {
		if (!GameStateStore.instance) {
			GameStateStore.instance = new GameStateStore(myPlayerId);
		}
		return GameStateStore.instance;
	}

	// ── Queries ────────────────────────────────────────────────────────

	get state(): ClientGameState | null {
		return this._state;
	}

	get myPlayerId(): string {
		return this._myPlayerId;
	}

	get validActions(): ValidAction[] {
		return this._validActions;
	}

	get isMyTurn(): boolean {
		return this._state?.active_player_id === this._myPlayerId;
	}

	get currentPhase(): TurnPhase | null {
		return this._state?.current_phase ?? null;
	}

	getCard(instanceId: string): ClientCard | undefined {
		return this._state?.cards[instanceId];
	}

	getCardsInZone(playerId: string, zone: Zone): ClientCard[] {
		const player = this._state?.players[playerId];
		if (!player) return [];
		const zoneState = player.zones?.[zone as string];
		if (!zoneState?.card_ids) return [];
		return zoneState.card_ids
			.map((id) => this._state!.cards[id])
			.filter(Boolean);
	}

	getMyCardsInZone(zone: Zone): ClientCard[] {
		return this.getCardsInZone(this._myPlayerId, zone);
	}

	getOpponentCardsInZone(zone: Zone): ClientCard[] {
		const opponentId = this.getOpponentId();
		return opponentId ? this.getCardsInZone(opponentId, zone) : [];
	}

	getOpponentId(): string | null {
		if (!this._state) return null;
		for (const pid of Object.keys(this._state.players)) {
			if (pid !== this._myPlayerId) return pid;
		}
		return null;
	}

	// ── State application ─────────────────────────────────────────────

	applyServerState(raw: Record<string, unknown>): void {
		const rawState: GameStateForPlayer = raw as never;
		const rawCards = (rawState.cards ?? {}) as Record<string, GameCard>;

		const cards: Record<string, ClientCard> = {};
		for (const [cid, rc] of Object.entries(rawCards)) {
			cards[cid] = { ...rc, faceUp: (rc.card_id ?? 0) > 0 };
		}

		this._state = { ...(rawState as object), cards } as ClientGameState;
	}

	updateValidActions(actions: ValidAction[]): void {
		this._validActions = actions;
	}

	// ── Cleanup ──────────────────────────────────────────────────────

	dispose(): void {
		this._state = null;
		this._validActions = [];
		GameStateStore.instance = null;
	}
}
