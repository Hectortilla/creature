/**
 * Game networking module
 *
 * Provides WebSocket-based game communication that can be used
 * from both Svelte components and Babylon scene scripts.
 */

export { default as GameConnection } from './GameConnection';
export { CardDefinitionCache } from './CardDefinitionCache';
export type { CardDefinition } from './CardDefinitionCache';
export type {
	ValidAction,
	GameMessage,
	ActionData
} from './types';
export { CardVisualState } from './models';
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
	ClientCard,
	ClientPlayerState,
	ClientGameState,
} from './models';
