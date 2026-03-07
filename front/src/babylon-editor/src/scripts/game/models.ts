/**
 * Client-only types that supplement the auto-generated backend types.
 * All backend domain types come from `$lib/api/types.gen.ts` via `npm run generate`.
 */

export type {
	Zone,
	TurnPhase,
	GameStatus,
	DamageType,
	GameState,
	GameConfiguration,
	GameRoom,
	ValidActionSchema,
	ActionResultData,
	GameStartedData,
	GameStateData,
	ValidActionsData,
	CardDrawnEvent,
	CardMovedEvent,
	CardPlayedEvent,
	CardPromotedEvent,
	CardSwappedEvent,
	CardAssociatedEvent,
	CardEvolvedEvent,
	AttackDeclaredEvent,
	DamageDealtEvent,
	CardDestroyedEvent,
	ElementsConsumedEvent,
	ElementsRestoredEvent,
	TurnStartedEvent,
	TurnEndedEvent,
	PhaseChangedEvent,
	GameStartedEvent,
	GameEndedEvent,
	NoDefenderEvent,
	EffectTriggeredEvent,
	EffectAppliedEvent,
	ElementContribution,
	ElementPool,
	AttackDefinition,
	ZoneState,
} from '$lib/api/types.gen';

import type {
	Zone,
	TurnPhase,
	GameStatus,
	GameConfiguration,
	AttackDefinition,
	ElementContribution,
	ElementPool,
	ZoneState,
} from '$lib/api/types.gen';

export enum CardVisualState {
	IDLE = 'IDLE',
	HOVERED = 'HOVERED',
	SELECTED = 'SELECTED',
	DRAGGING = 'DRAGGING',
	ANIMATING = 'ANIMATING',
	DISABLED = 'DISABLED',
}

/**
 * Client-side card representation.
 *
 * Built incrementally from backend events + CardDefinitionCache lookups.
 * The backend excludes GameCard from the serialized GameState, so the
 * client constructs these from CardDrawnEvent / CardPlayedEvent data.
 */
export interface ClientCard {
	instanceId: string;
	cardId: number;
	ownerId: string;
	name: string;
	zone: Zone;
	currentHealth: number;
	maxHealth: number;
	physicalDefence: number;
	magicDefence: number;
	isAlive: boolean;
	/** false when the card identity is hidden (opponent draw) */
	faceUp: boolean;
	attacks?: AttackDefinition[];
	elementContribution?: ElementContribution[];
}

/** Client-side player state, built from events. */
export interface ClientPlayerState {
	playerId: string;
	name: string;
	zones: Record<string, ZoneState>;
	elementPool: ElementPool;
}

/**
 * Full client-side game state.
 *
 * Mirrors the backend GameState fields that are serialized (game_id,
 * turn_number, etc.) and adds client-owned data that the backend
 * excludes (cards map, per-player zones).
 */
export interface ClientGameState {
	gameId: string;
	activePlayerId: string | null;
	turnNumber: number;
	currentPhase: TurnPhase;
	status: GameStatus;
	winnerId: string | null;
	config: GameConfiguration | null;
	players: Record<string, ClientPlayerState>;
	cards: Record<string, ClientCard>;
}
