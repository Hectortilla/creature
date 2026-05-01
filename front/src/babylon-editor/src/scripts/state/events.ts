/**
 * Typed event data interfaces and event map for the BoardController event bus.
 *
 * Every event payload is self-contained: subscribers never need to query
 * GameStateStore.  Derived fields (isMyTurn, full element pools, etc.)
 * are computed by BoardController before emission.
 */

import type {
	Zone,
	TurnPhase,
	ClientCard,
	ClientGameState,
} from '../game/models';
// Note: event data interfaces use their own camelCase field names.
// These are populated by BoardController from raw server events.

import type { ValidAction } from '../game/types';

// ============================================================================
// Event data interfaces
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
	isMyTurn: boolean;
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
	elements: Record<string, number>;
	currentPool: Record<string, number>;
	maxPool: Record<string, number>;
}

export interface ElementPoolsUpdatedData {
	myPool: { elements: Record<string, number>; maxElements: Record<string, number> };
	oppPool: { elements: Record<string, number>; maxElements: Record<string, number> };
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

export interface ValidActionsChangedData {
	actions: ValidAction[];
	isMyTurn: boolean;
}

export interface ActionFailedData {
	error: string;
	errorCode: string | null;
}

export interface GameStartedEventData {
	state: ClientGameState;
	myPlayerId: string;
	opponentId: string;
	isMyTurn: boolean;
	currentPhase: TurnPhase;
	deckSize: number;
	myElementPool: { elements: Record<string, number>; maxElements: Record<string, number> };
	opponentElementPool: { elements: Record<string, number>; maxElements: Record<string, number> };
}

// ============================================================================
// Typed event map
// ============================================================================

export interface StateChangeEvents {
	cardAdded: ClientCard;
	cardMoved: CardMovedData;
	cardHealthChanged: CardHealthChangedData;
	cardDestroyed: CardDestroyedData;
	phaseChanged: PhaseChangedData;
	turnChanged: TurnChangedData;
	gameStarted: GameStartedEventData;
	gameOver: GameOverData;
	validActionsChanged: ValidActionsChangedData;
	stateReplaced: ClientGameState;
	attackDeclared: AttackDeclaredData;
	cardAssociated: CardAssociatedData;
	cardEvolved: CardEvolvedData;
	elementsConsumed: ElementsChangedData;
	elementsRestored: ElementsChangedData;
	elementPoolsUpdated: ElementPoolsUpdatedData;
	noDefender: NoDefenderData;
	effectTriggered: EffectTriggeredData;
	effectApplied: EffectAppliedData;
	cardsSwapped: CardsSwappedData;
	turnEnded: { playerId: string; turnNumber: number };
	actionFailed: ActionFailedData;
}

export type StateChangeCallback<T> = (data: T) => void;
