import type InteractionManager from '../interaction/InteractionManager';
import type { ClientCard } from '../game/models';
import type {
	HoveredCardPayload,
	HoveredCardSetter,
	IngameCardState,
} from '$lib/stores/hoveredCard';

/**
 * Per-frame bridge between Babylon hover state and the Svelte overlay store.
 *
 * Diffs on a signature that captures live-state fields so HP drops and
 * affordability changes propagate mid-hover, not only on hover transitions.
 */
export class HoveredCardBridge {
	private _interactionManager: InteractionManager;
	private _setter: HoveredCardSetter | null = null;
	private _lastSignature: string | null = null;

	constructor(interactionManager: InteractionManager) {
		this._interactionManager = interactionManager;
	}

	setSetter(fn: HoveredCardSetter): void {
		this._setter = fn;
	}

	update(): void {
		if (!this._setter) return;

		const entity = this._interactionManager.hoveredEntity;
		if (!entity) {
			this._emitIfChanged(null, null);
			return;
		}

		const card = entity.cardData;
		if (!card.faceUp) {
			this._emitIfChanged(null, null);
			return;
		}

		const affordable = this._affordableAttackIds(card);
		const signature = this._signatureOf(card, affordable);
		if (signature === this._lastSignature) return;

		const payload: HoveredCardPayload = {
			cardId: card.card_id,
			instanceId: card.instance_id,
			ingame: this._buildIngameState(card, affordable),
		};
		this._emitIfChanged(payload, signature);
	}

	private _emitIfChanged(payload: HoveredCardPayload | null, signature: string | null): void {
		if (signature === this._lastSignature) return;
		this._lastSignature = signature;
		this._setter?.(payload);
	}

	private _buildIngameState(card: ClientCard, affordable: Set<number>): IngameCardState {
		return {
			instanceId: card.instance_id,
			zone: card.zone ?? '',
			status: card.status ?? '',
			isAlive: card.is_alive,
			turnsInZone: card.turns_in_zone ?? 0,
			hasAttackedThisTurn: card.has_attacked_this_turn ?? false,
			swappedThisTurn: card.swapped_this_turn ?? false,
			canAttack: card.can_attack,
			canPromote: card.can_promote,
			canEvolve: card.can_evolve,
			currentHealth: card.current_health,
			maxHealth: card.health,
			attacks: card.attacks ?? [],
			affordableAttackIds: affordable,
		};
	}

	private _signatureOf(card: ClientCard, affordable: Set<number>): string {
		return [
			card.instance_id,
			card.current_health,
			card.has_attacked_this_turn ? 1 : 0,
			card.swapped_this_turn ? 1 : 0,
			affordable.size,
		].join('|');
	}

	private _affordableAttackIds(card: ClientCard): Set<number> {
		const actions = this._interactionManager.actionBuilder.getActionsForCard(card.instance_id);
		const attackActions = actions.filter((a) => a.action === 'attack');
		if (attackActions.length === 0) {
			return new Set((card.attacks ?? []).map((a) => a.attack_id));
		}
		const ids = new Set<number>();
		for (const a of attackActions) {
			if (typeof a.attack_id === 'number') ids.add(a.attack_id);
		}
		return ids;
	}
}
