import { writable, type Writable } from 'svelte/store';
import type { AttackDefinition } from '$lib/api/types.gen';

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

export type HoveredCardSetter = (payload: HoveredCardPayload | null) => void;

export const hoveredCard: Writable<HoveredCardPayload | null> = writable(null);

export const setHoveredCard: HoveredCardSetter = (payload) => hoveredCard.set(payload);
