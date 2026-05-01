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
	GameCard,
	CardStatus,
	PlayerState,
	GameStateForPlayer,
} from '$lib/api/types.gen';

import type {
	Zone,
	GameCard,
	GameStateForPlayer,
} from '$lib/api/types.gen';
import { Quaternion, Vector3 } from '@babylonjs/core/Maths/math.vector';

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
 * Extends the auto-generated GameCard type with the client-only `faceUp` field
 * used for visibility control (opponent's hand cards are face-down).
 */
export type ClientCard = GameCard & {
	/** false when the card identity is hidden (opponent draw) */
	faceUp: boolean;
};

/** Creates a minimal ClientCard for a face-down placeholder (e.g. deck stack). */
export function createFaceDownCard(instanceId: string, ownerId: string, zone: Zone = 'DECK'): ClientCard {
	return {
		instance_id: instanceId,
		card_id: 0,
		owner_id: ownerId,
		name: '',
		zone,
		current_health: 0,
		health: 0,
		physical_defence: 0,
		magic_defence: 0,
		is_alive: false,
		faceUp: false,
		can_attack: false,
		can_promote: false,
		can_evolve: false,
	};
}

/**
 * Full client-side game state.
 *
 * Extends the auto-generated GameStateForPlayer, overriding `cards` to use
 * ClientCard (which adds the client-only `faceUp` field).
 */
export type ClientGameState = Omit<GameStateForPlayer, 'cards'> & {
	cards: Record<string, ClientCard>;
};

const DEG_TO_RAD = Math.PI / 180;

export function getDeactivationAngle(card: ClientCard): number {
	if (card.has_attacked_this_turn) return 90;
	if (card.zone === 'SUPPORTING' && card.turns_in_zone === 0 && !card.swapped_this_turn) {
		return 90;
	}
	if (card.swapped_this_turn) return 45;
	return 0;
}

export function getDeactivationQuaternion(card: ClientCard): Quaternion {
	const angle = getDeactivationAngle(card);
	if (angle === 0) return Quaternion.Identity();
	return Quaternion.RotationAxis(Vector3.Up(), angle * DEG_TO_RAD);
}
