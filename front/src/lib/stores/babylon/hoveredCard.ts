import type { AttackDefinition } from '$lib/api/types.gen';
import { createHudStore, type HudStoreSetter } from './createHudStore';

export interface IngameCardState {
	instanceId: string;
	zone: string;
	status: string;
	isAlive: boolean;
	turnsInZone: number;
	hasAttackedThisTurn: boolean;
	swappedThisTurn: boolean;
	canAttack: boolean;
	canPromote: boolean;
	canEvolve: boolean;
	currentHealth: number;
	maxHealth: number;
	attacks: AttackDefinition[];
	affordableAttackIds: Set<number>;
}

export interface HoveredCardPayload {
	cardId: number;
	instanceId: string;
	ingame: IngameCardState;
}

export type HoveredCardSetter = HudStoreSetter<HoveredCardPayload>;

export const [hoveredCard, setHoveredCard] = createHudStore<HoveredCardPayload>();
