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
	ClientPlayerState,
	ClientGameState,
	GameConfiguration,
	ZoneState,
} from '../game/models';

import type { ValidAction } from '../game/types';

const ALL_ZONES: Zone[] = ['DECK', 'HAND', 'SUPPORTING', 'ATTACKING', 'GRAVEYARD'] as Zone[];

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
		return this._state?.activePlayerId === this._myPlayerId;
	}

	get currentPhase(): TurnPhase | null {
		return this._state?.currentPhase ?? null;
	}

	getCard(instanceId: string): ClientCard | undefined {
		return this._state?.cards[instanceId];
	}

	getCardsInZone(playerId: string, zone: Zone): ClientCard[] {
		const player = this._state?.players[playerId];
		if (!player) return [];
		const zoneState = player.zones[zone as string];
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
		const rawPlayers = raw.players as Record<string, Record<string, unknown>> | undefined;
		const rawCards = raw.cards as Record<string, Record<string, unknown>> | undefined;

		const players: Record<string, ClientPlayerState> = {};
		if (rawPlayers) {
			for (const [pid, rp] of Object.entries(rawPlayers)) {
				players[pid] = {
					playerId: (rp.player_id as string) ?? pid,
					name: (rp.name as string) ?? pid,
					zones: (rp.zones as Record<string, ZoneState>) ?? this._emptyZones(pid),
					elementPool: (rp.element_pool as ClientPlayerState['elementPool']) ?? { elements: {}, max_elements: {} },
				};
			}
		}

		const cards: Record<string, ClientCard> = {};
		if (rawCards) {
			for (const [cid, rc] of Object.entries(rawCards)) {
				cards[cid] = {
					instanceId: (rc.instance_id as string) ?? cid,
					cardId: (rc.card_id as number) ?? 0,
					ownerId: (rc.owner_id as string) ?? '',
					name: (rc.name as string) ?? '',
					zone: (rc.zone as Zone) ?? ('DECK' as Zone),
					currentHealth: (rc.current_health as number) ?? 0,
					maxHealth: (rc.health as number) ?? 0,
					physicalDefence: (rc.physical_defence as number) ?? 0,
					magicDefence: (rc.magic_defence as number) ?? 0,
					isAlive: (rc.is_alive as boolean) ?? true,
					faceUp: ((rc.card_id as number) ?? 0) > 0,
					attacks: rc.attacks as ClientCard['attacks'],
					elementContribution: rc.element_contribution as ClientCard['elementContribution'],
				};
			}
		}

		this._state = {
			gameId: (raw.game_id as string) ?? '',
			activePlayerId: (raw.active_player_id as string) ?? null,
			turnNumber: (raw.turn_number as number) ?? 0,
			currentPhase: (raw.current_phase as TurnPhase) ?? ('DRAW' as TurnPhase),
			status: (raw.status as ClientGameState['status']) ?? ('WAITING' as ClientGameState['status']),
			winnerId: (raw.winner_id as string) ?? null,
			config: (raw.config as GameConfiguration) ?? null,
			players,
			cards,
		};
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

	// ── Private ──────────────────────────────────────────────────────

	private _emptyZones(playerId: string): Record<string, ZoneState> {
		const zones: Record<string, ZoneState> = {};
		for (const z of ALL_ZONES) {
			zones[z as string] = { zone: z, owner_id: playerId, card_ids: [], is_full: false };
		}
		return zones;
	}
}
