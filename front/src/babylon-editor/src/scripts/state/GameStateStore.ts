/**
 * GameStateStore — central client-side game state singleton.
 *
 * Single source of truth for all game data. Every other system (zones,
 * animations, interaction, HUD) reads from it. Processes raw backend
 * events to build and maintain a ClientGameState.
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
import { CardDefinitionCache } from '../game/CardDefinitionCache';
import type { CardDefinition } from '../game/CardDefinitionCache';

// ============================================================================
// Change-event data interfaces
// ============================================================================

export interface CardMovedData {
	instanceId: string;
	ownerId: string;
	fromZone: Zone;
	toZone: Zone;
}

export interface CardHealthChangedData {
	instanceId: string;
	oldHealth: number;
	newHealth: number;
	maxHealth: number;
}

export interface PhaseChangedData {
	fromPhase: TurnPhase;
	toPhase: TurnPhase;
	playerId: string;
}

export interface TurnChangedData {
	playerId: string;
	turnNumber: number;
	isFirstTurn: boolean;
}

export interface CardDestroyedData {
	instanceId: string;
	ownerId: string;
	cardName: string;
}

export interface GameOverData {
	winnerId: string;
	loserId: string;
	reason: string;
}

export interface AttackDeclaredData {
	attackerOwnerId: string;
	attackerId: string;
	targetId: string;
	attackId: number;
	attackName: string;
}

export interface CardAssociatedData {
	playerId: string;
	associationCardId: string;
	targetCardId: string;
	cardId: number;
	sourceZone: string | null;
}

export interface CardEvolvedData {
	playerId: string;
	baseCardId: string;
	evolutionCardId: string;
	cardId: number;
	baseCardName: string;
	evolutionCardName: string;
}

export interface ElementsChangedData {
	playerId: string;
	elements: Record<number, number>;
}

export interface NoDefenderData {
	defenderId: string;
	attackerId: string;
	mustDefend: boolean;
	gameLost: boolean;
}

export interface EffectTriggeredData {
	sourceCardId: string;
	effectId: string;
	effectName: string;
	triggerReason: string;
}

export interface EffectAppliedData {
	effectId: string;
	affectedCardIds: string[];
	description: string;
}

export interface CardsSwappedData {
	ownerId: string;
	supportingId: string;
	attackingId: string;
}

// ============================================================================
// Typed change event map
// ============================================================================

export interface StateChangeEvents {
	cardAdded: ClientCard;
	cardMoved: CardMovedData;
	cardHealthChanged: CardHealthChangedData;
	cardDestroyed: CardDestroyedData;
	phaseChanged: PhaseChangedData;
	turnChanged: TurnChangedData;
	gameStarted: ClientGameState;
	gameOver: GameOverData;
	validActionsChanged: ValidAction[];
	stateReplaced: ClientGameState;
	attackDeclared: AttackDeclaredData;
	cardAssociated: CardAssociatedData;
	cardEvolved: CardEvolvedData;
	elementsConsumed: ElementsChangedData;
	elementsRestored: ElementsChangedData;
	noDefender: NoDefenderData;
	effectTriggered: EffectTriggeredData;
	effectApplied: EffectAppliedData;
	cardsSwapped: CardsSwappedData;
	turnEnded: { playerId: string; turnNumber: number };
}

type StateChangeCallback<T> = (data: T) => void;

// ============================================================================
// Zone constants (string values matching backend Zone enum)
// ============================================================================

const ZONE_DECK: Zone = 'DECK' as Zone;
const ZONE_HAND: Zone = 'HAND' as Zone;
const ZONE_SUPPORTING: Zone = 'SUPPORTING' as Zone;
const ZONE_ATTACKING: Zone = 'ATTACKING' as Zone;
const ZONE_GRAVEYARD: Zone = 'GRAVEYARD' as Zone;

const ALL_ZONES: Zone[] = [ZONE_DECK, ZONE_HAND, ZONE_SUPPORTING, ZONE_ATTACKING, ZONE_GRAVEYARD];

// ============================================================================
// GameStateStore
// ============================================================================

export class GameStateStore {
	static instance: GameStateStore | null = null;

	private _state: ClientGameState | null = null;
	private _myPlayerId = '';
	private _validActions: ValidAction[] = [];
	private _listeners = new Map<keyof StateChangeEvents, Set<StateChangeCallback<any>>>();

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
		const opponentId = this._getOpponentId();
		return opponentId ? this.getCardsInZone(opponentId, zone) : [];
	}

	getOpponentId(): string | null {
		return this._getOpponentId();
	}

	// ── Event Processing (called by BoardController) ───────────────────

	processGameStarted(data: Record<string, unknown>): void {
		const rawState = data.game_state as Record<string, unknown> | undefined;
		const rawEvents = data.events as Record<string, unknown>[] | undefined;
		const rawActions = data.valid_actions as ValidAction[] | undefined;

		this._initStateFromServer(rawState ?? {});
		if (rawEvents) this.processGameEvents(rawEvents);
		if (rawActions) this.updateValidActions(rawActions);

		this._emit('gameStarted', this._state!);
	}

	processGameEvents(events: Record<string, unknown>[]): void {
		for (const raw of events) {
			this._processEvent(raw);
		}
	}

	processGameState(rawState: Record<string, unknown>): void {
		this._initStateFromServer(rawState);
		this._emit('stateReplaced', this._state!);
	}

	updateValidActions(actions: ValidAction[]): void {
		this._validActions = actions;
		this._emit('validActionsChanged', this._validActions);
	}

	// ── Change Subscriptions ─────────────────────────────────────────

	on<K extends keyof StateChangeEvents>(
		event: K,
		cb: StateChangeCallback<StateChangeEvents[K]>,
	): void {
		if (!this._listeners.has(event)) {
			this._listeners.set(event, new Set());
		}
		this._listeners.get(event)!.add(cb);
	}

	off<K extends keyof StateChangeEvents>(
		event: K,
		cb: StateChangeCallback<StateChangeEvents[K]>,
	): void {
		this._listeners.get(event)?.delete(cb);
	}

	// ── Cleanup ──────────────────────────────────────────────────────

	dispose(): void {
		this._state = null;
		this._validActions = [];
		this._listeners.clear();
		GameStateStore.instance = null;
	}

	// ====================================================================
	// Private helpers
	// ====================================================================

	private _emit<K extends keyof StateChangeEvents>(
		event: K,
		data: StateChangeEvents[K],
	): void {
		const listeners = this._listeners.get(event);
		console.log('emit', event, data, listeners);

		
		if (!listeners) return;
		for (const cb of listeners) cb(data);
	}

	private _getOpponentId(): string | null {
		if (!this._state) return null;
		for (const pid of Object.keys(this._state.players)) {
			if (pid !== this._myPlayerId) return pid;
		}
		return null;
	}

	// ── State initialisation from server payload ─────────────────────

	private _initStateFromServer(raw: Record<string, unknown>): void {
		this._state = {
			gameId: (raw.game_id as string) ?? '',
			activePlayerId: (raw.active_player_id as string) ?? null,
			turnNumber: (raw.turn_number as number) ?? 0,
			currentPhase: (raw.current_phase as TurnPhase) ?? ('DRAW' as TurnPhase),
			status: (raw.status as ClientGameState['status']) ?? ('WAITING' as ClientGameState['status']),
			winnerId: (raw.winner_id as string) ?? null,
			config: (raw.config as GameConfiguration) ?? null,
			players: this._state?.players ?? {},
			cards: this._state?.cards ?? {},
		};
	}

	/** Ensure a player entry exists in state.players. */
	private _ensurePlayer(playerId: string): ClientPlayerState {
		if (!this._state) throw new Error('GameStateStore: state not initialised');
		let player = this._state.players[playerId];
		if (!player) {
			const zones: Record<string, ZoneState> = {};
			for (const z of ALL_ZONES) {
				zones[z as string] = {
					zone: z,
					owner_id: playerId,
					card_ids: [],
					is_full: false,
				};
			}
			player = {
				playerId,
				name: playerId,
				zones,
				elementPool: { elements: {}, max_elements: {} },
			};
			this._state.players[playerId] = player;
		}
		return player;
	}

	/** Move a card id between zone arrays for a player. */
	private _moveCardBetweenZones(
		playerId: string,
		instanceId: string,
		fromZone: Zone,
		toZone: Zone,
	): void {
		const player = this._ensurePlayer(playerId);
		const from = player.zones[fromZone as string];
		const to = player.zones[toZone as string];
		if (from?.card_ids) {
			const idx = from.card_ids.indexOf(instanceId);
			if (idx !== -1) from.card_ids.splice(idx, 1);
		}
		if (to?.card_ids && !to.card_ids.includes(instanceId)) {
			to.card_ids.push(instanceId);
		}
	}

	/** Build a ClientCard from a CardDefinitionCache entry, or a minimal stub. */
	private _buildClientCard(
		instanceId: string,
		cardId: number,
		ownerId: string,
		zone: Zone,
		faceUp: boolean,
	): ClientCard {
		const cache = CardDefinitionCache.instance;
		const def: CardDefinition | undefined =
			cardId > 0 ? cache?.getByCardId(cardId) : undefined;

		if (cardId > 0) cache?.registerInstance(instanceId, cardId);

		return {
			instanceId,
			cardId,
			ownerId,
			name: def?.name ?? '',
			zone,
			currentHealth: def?.health ?? 0,
			maxHealth: def?.health ?? 0,
			physicalDefence: def?.physical_defence ?? 0,
			magicDefence: def?.magic_defence ?? 0,
			isAlive: true,
			faceUp,
		};
	}

	// ── Single-event dispatch ────────────────────────────────────────

	private _processEvent(raw: Record<string, unknown>): void {
		const eventType = raw.event_type as string | undefined;
		if (!eventType || !this._state) return;

		switch (eventType) {
			case 'CardDrawnEvent':
				return this._handleCardDrawn(raw);
			case 'CardMovedEvent':
				return this._handleCardMoved(raw);
			case 'CardPlayedEvent':
				return this._handleCardPlayed(raw);
			case 'CardPromotedEvent':
				return this._handleCardPromoted(raw);
			case 'CardSwappedEvent':
				return this._handleCardSwapped(raw);
			case 'CardAssociatedEvent':
				return this._handleCardAssociated(raw);
			case 'CardEvolvedEvent':
				return this._handleCardEvolved(raw);
			case 'AttackDeclaredEvent':
				return this._handleAttackDeclared(raw);
			case 'DamageDealtEvent':
				return this._handleDamageDealt(raw);
			case 'CardDestroyedEvent':
				return this._handleCardDestroyed(raw);
			case 'ElementsConsumedEvent':
				return this._handleElementsConsumed(raw);
			case 'ElementsRestoredEvent':
				return this._handleElementsRestored(raw);
			case 'TurnStartedEvent':
				return this._handleTurnStarted(raw);
			case 'TurnEndedEvent':
				return this._handleTurnEnded(raw);
			case 'PhaseChangedEvent':
				return this._handlePhaseChanged(raw);
			case 'GameStartedEvent':
				return this._handleGameStartedEvent(raw);
			case 'GameEndedEvent':
				return this._handleGameEnded(raw);
			case 'NoDefenderEvent':
				return this._handleNoDefender(raw);
			case 'EffectTriggeredEvent':
				return this._handleEffectTriggered(raw);
			case 'EffectAppliedEvent':
				return this._handleEffectApplied(raw);
			default:
				console.warn(`GameStateStore: unhandled event type "${eventType}"`);
		}
	}

	// ── Event handlers ───────────────────────────────────────────────

	private _handleCardDrawn(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		const instanceId = raw.instance_id as string;
		const cardId = raw.card_id as number;
		const isMine = playerId === this._myPlayerId;
		const hasIdentity = !!instanceId && cardId > 0;

		this._ensurePlayer(playerId);

		const card = this._buildClientCard(
			hasIdentity ? instanceId : `opponent-${Date.now()}-${Math.random()}`,
			hasIdentity ? cardId : 0,
			playerId,
			ZONE_HAND,
			isMine && hasIdentity,
		);

		this._state!.cards[card.instanceId] = card;
		this._moveCardBetweenZones(playerId, card.instanceId, ZONE_DECK, ZONE_HAND);

		this._emit('cardAdded', card);
		this._emit('cardMoved', {
			instanceId: card.instanceId,
			ownerId: playerId,
			fromZone: ZONE_DECK,
			toZone: ZONE_HAND,
		});
	}

	private _handleCardMoved(raw: Record<string, unknown>): void {
		const instanceId = raw.instance_id as string;
		const ownerId = raw.owner_id as string;
		const fromZone = raw.from_zone as Zone;
		const toZone = raw.to_zone as Zone;
		if (!fromZone || !toZone) return;

		const card = this._state!.cards[instanceId];
		if (card) card.zone = toZone;

		this._moveCardBetweenZones(ownerId, instanceId, fromZone, toZone);
		this._emit('cardMoved', { instanceId, ownerId, fromZone, toZone });
	}

	private _handleCardPlayed(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		const instanceId = raw.instance_id as string;

		const card = this._state!.cards[instanceId];
		if (card) card.zone = ZONE_SUPPORTING;

		this._moveCardBetweenZones(playerId, instanceId, ZONE_HAND, ZONE_SUPPORTING);
		this._emit('cardMoved', {
			instanceId,
			ownerId: playerId,
			fromZone: ZONE_HAND,
			toZone: ZONE_SUPPORTING,
		});
	}

	private _handleCardPromoted(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		const instanceId = raw.instance_id as string;

		const card = this._state!.cards[instanceId];
		if (card) card.zone = ZONE_ATTACKING;

		this._moveCardBetweenZones(playerId, instanceId, ZONE_SUPPORTING, ZONE_ATTACKING);
		this._emit('cardMoved', {
			instanceId,
			ownerId: playerId,
			fromZone: ZONE_SUPPORTING,
			toZone: ZONE_ATTACKING,
		});
	}

	private _handleCardSwapped(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		const supportingId = raw.supporting_card_id as string;
		const attackingId = raw.attacking_card_id as string;

		const sup = this._state!.cards[supportingId];
		const atk = this._state!.cards[attackingId];
		if (sup) sup.zone = ZONE_ATTACKING;
		if (atk) atk.zone = ZONE_SUPPORTING;

		this._moveCardBetweenZones(playerId, supportingId, ZONE_SUPPORTING, ZONE_ATTACKING);
		this._moveCardBetweenZones(playerId, attackingId, ZONE_ATTACKING, ZONE_SUPPORTING);

		this._emit('cardsSwapped', {
			ownerId: playerId,
			supportingId,
			attackingId,
		});

		this._emit('cardMoved', {
			instanceId: supportingId,
			ownerId: playerId,
			fromZone: ZONE_SUPPORTING,
			toZone: ZONE_ATTACKING,
		});
		this._emit('cardMoved', {
			instanceId: attackingId,
			ownerId: playerId,
			fromZone: ZONE_ATTACKING,
			toZone: ZONE_SUPPORTING,
		});
	}

	private _handleCardAssociated(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		const associationCardId = raw.association_card_id as string;
		const targetCardId = raw.target_card_id as string;
		const cardId = (raw.card_id as number) ?? 0;
		const sourceZone = (raw.source_zone as Zone) ?? null;

		if (sourceZone) {
			this._moveCardBetweenZones(playerId, associationCardId, sourceZone, ZONE_SUPPORTING);
			const card = this._state!.cards[associationCardId];
			if (card) card.zone = ZONE_SUPPORTING;

			this._emit('cardMoved', {
				instanceId: associationCardId,
				ownerId: playerId,
				fromZone: sourceZone,
				toZone: ZONE_SUPPORTING,
			});
		}

		this._emit('cardAssociated', {
			playerId,
			associationCardId,
			targetCardId,
			cardId,
			sourceZone: sourceZone as string | null,
		});
	}

	private _handleCardEvolved(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		const baseCardId = raw.base_card_id as string;
		const evolutionCardId = raw.evolution_card_id as string;
		const cardId = (raw.card_id as number) ?? 0;
		const baseCardName = (raw.base_card_name as string) ?? '';
		const evolutionCardName = (raw.evolution_card_name as string) ?? '';

		const baseCard = this._state!.cards[baseCardId];
		if (baseCard) {
			const evoCard = this._buildClientCard(
				evolutionCardId,
				cardId,
				playerId,
				baseCard.zone,
				baseCard.faceUp,
			);
			this._state!.cards[evolutionCardId] = evoCard;

			const player = this._ensurePlayer(playerId);
			const zoneState = player.zones[baseCard.zone as string];
			if (zoneState?.card_ids) {
				const idx = zoneState.card_ids.indexOf(baseCardId);
				if (idx !== -1) zoneState.card_ids[idx] = evolutionCardId;
			}
			delete this._state!.cards[baseCardId];
		}

		this._emit('cardEvolved', {
			playerId,
			baseCardId,
			evolutionCardId,
			cardId,
			baseCardName,
			evolutionCardName,
		});
	}

	private _handleAttackDeclared(raw: Record<string, unknown>): void {
		this._emit('attackDeclared', {
			attackerOwnerId: raw.attacker_owner_id as string,
			attackerId: raw.attacker_id as string,
			targetId: raw.target_id as string,
			attackId: (raw.attack_id as number) ?? 0,
			attackName: (raw.attack_name as string) ?? '',
		});
	}

	private _handleDamageDealt(raw: Record<string, unknown>): void {
		const targetId = raw.target_id as string;
		const finalDamage = (raw.final_damage as number) ?? 0;
		const remainingHealth = (raw.remaining_health as number) ?? 0;

		const card = this._state!.cards[targetId];
		if (!card) return;

		const oldHealth = card.currentHealth;
		card.currentHealth = remainingHealth;
		if (card.currentHealth <= 0) card.isAlive = false;

		this._emit('cardHealthChanged', {
			instanceId: targetId,
			oldHealth,
			newHealth: card.currentHealth,
			maxHealth: card.maxHealth,
		});
	}

	private _handleCardDestroyed(raw: Record<string, unknown>): void {
		const instanceId = raw.instance_id as string;
		const ownerId = raw.owner_id as string;
		const cardName = (raw.card_name as string) ?? '';

		const card = this._state!.cards[instanceId];
		const fromZone = card?.zone ?? ZONE_ATTACKING;
		if (card) {
			card.isAlive = false;
			card.zone = ZONE_GRAVEYARD;
		}

		this._moveCardBetweenZones(ownerId, instanceId, fromZone, ZONE_GRAVEYARD);

		this._emit('cardDestroyed', { instanceId, ownerId, cardName });
		this._emit('cardMoved', {
			instanceId,
			ownerId,
			fromZone,
			toZone: ZONE_GRAVEYARD,
		});
	}

	private _handleElementsConsumed(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		const elements = (raw.elements as Record<number, number>) ?? {};

		const player = this._ensurePlayer(playerId);
		const pool = player.elementPool;
		if (!pool.elements) pool.elements = {};
		for (const [elemIdStr, amount] of Object.entries(elements)) {
			const current = pool.elements[elemIdStr] ?? 0;
			pool.elements[elemIdStr] = Math.max(0, current - (amount as number));
		}

		this._emit('elementsConsumed', { playerId, elements });
	}

	private _handleElementsRestored(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		const elements = (raw.elements as Record<number, number>) ?? {};

		const player = this._ensurePlayer(playerId);
		const pool = player.elementPool;
		if (!pool.elements) pool.elements = {};
		if (!pool.max_elements) pool.max_elements = {};
		for (const [elemIdStr, amount] of Object.entries(elements)) {
			pool.elements[elemIdStr] = amount as number;
			pool.max_elements[elemIdStr] = amount as number;
		}

		this._emit('elementsRestored', { playerId, elements });
	}

	private _handleTurnStarted(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		const turnNumber = (raw.turn_number as number) ?? 0;
		const isFirstTurn = (raw.is_first_turn as boolean) ?? false;

		this._state!.activePlayerId = playerId;
		this._state!.turnNumber = turnNumber;

		this._emit('turnChanged', { playerId, turnNumber, isFirstTurn });
	}

	private _handleTurnEnded(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		const turnNumber = (raw.turn_number as number) ?? 0;
		this._emit('turnEnded', { playerId, turnNumber });
	}

	private _handlePhaseChanged(raw: Record<string, unknown>): void {
		const playerId = raw.player_id as string;
		const fromPhase = raw.from_phase as TurnPhase;
		const toPhase = raw.to_phase as TurnPhase;
		if (!toPhase) return;

		this._state!.currentPhase = toPhase;
		this._emit('phaseChanged', { fromPhase, toPhase, playerId });
	}

	private _handleGameStartedEvent(raw: Record<string, unknown>): void {
		const playerIds = (raw.player_ids as string[]) ?? [];
		const firstPlayerId = (raw.first_player_id as string) ?? '';

		for (const pid of playerIds) this._ensurePlayer(pid);
		if (firstPlayerId) this._state!.activePlayerId = firstPlayerId;
	}

	private _handleGameEnded(raw: Record<string, unknown>): void {
		const winnerId = (raw.winner_id as string) ?? '';
		const loserId = (raw.loser_id as string) ?? '';
		const reason = (raw.reason as string) ?? '';

		this._state!.status = 'FINISHED' as ClientGameState['status'];
		this._state!.winnerId = winnerId;

		this._emit('gameOver', { winnerId, loserId, reason });
	}

	private _handleNoDefender(raw: Record<string, unknown>): void {
		this._emit('noDefender', {
			defenderId: (raw.defender_id as string) ?? '',
			attackerId: (raw.attacker_id as string) ?? '',
			mustDefend: (raw.must_defend as boolean) ?? false,
			gameLost: (raw.game_lost as boolean) ?? false,
		});
	}

	private _handleEffectTriggered(raw: Record<string, unknown>): void {
		this._emit('effectTriggered', {
			sourceCardId: (raw.source_card_id as string) ?? '',
			effectId: (raw.effect_id as string) ?? '',
			effectName: (raw.effect_name as string) ?? '',
			triggerReason: (raw.trigger_reason as string) ?? '',
		});
	}

	private _handleEffectApplied(raw: Record<string, unknown>): void {
		this._emit('effectApplied', {
			effectId: (raw.effect_id as string) ?? '',
			affectedCardIds: (raw.affected_card_ids as string[]) ?? [],
			description: (raw.description as string) ?? '',
		});
	}
}
