/**
 * ActionBuilder — bridge between backend valid_actions and the interactive board.
 *
 * Translates the flat list of ValidAction objects into card-level
 * affordances: "what can I do with this card?", "which cards should glow?",
 * "what are valid targets?". Never re-implements game rules.
 *
 * Pure TypeScript — no BabylonJS imports, no scene dependencies.
 * Has NO dependency on GameStateStore — receives validActions via setValidActions().
 */

import type GameConnection from '../game/GameConnection';
import type { ValidAction, ActionData } from '../game/types';

const SOURCE_CARD_FIELDS = [
	'instance_id',
	'attacker_id',
	'supporting_card_id',
	'attacking_card_id',
	'association_card_id',
	'evolution_card_id',
] as const;

const STRIP_FIELDS = new Set([
	'action', 'player_id', 'description', 'valid_phases',
	'card_name', 'attacker_name', 'attack_name', 'target_name',
	'supporting_card_name', 'attacking_card_name',
	'association_card_name', 'evolution_card_name',
	'cards',
]);

const NON_CARD_ACTIONS = new Set(['pass', 'concede']);

const TWO_STEP_ACTIONS: Record<string, { source: string; target: string }> = {
	attack:    { source: 'attacker_id',        target: 'target_card_id' },
	swap:      { source: 'supporting_card_id', target: 'attacking_card_id' },
	associate: { source: 'association_card_id', target: 'target_card_id' },
	evolve:    { source: 'evolution_card_id',   target: 'target_card_id' },
};

export class ActionBuilder {
	private _connection: GameConnection;
	private _validActions: ValidAction[] = [];

	constructor(connection: GameConnection) {
		this._connection = connection;
	}

	setValidActions(actions: ValidAction[]): void {
		this._validActions = actions;
	}

	// ── Card-level queries ──────────────────────────────────────────────

	getActionsForCard(instanceId: string): ValidAction[] {
		return this._validActions.filter(a => this._referencesCard(a, instanceId));
	}

	isCardInteractable(instanceId: string): boolean {
		return this._validActions.some(a => this._referencesCard(a, instanceId));
	}

	// ── Phase-level queries ─────────────────────────────────────────────

	getInteractableCardIds(): string[] {
		const ids = new Set<string>();
		for (const action of this._validActions) {
			if (NON_CARD_ACTIONS.has(action.action)) continue;
			this._collectSourceIds(action, ids);
		}
		return [...ids];
	}

	isTwoStepAction(action: ValidAction): boolean {
		return action.action in TWO_STEP_ACTIONS;
	}

	getValidTargetIds(action: ValidAction): string[] {
		return this.getValidTargets(action).targets;
	}

	/**
	 * Returns valid target instance IDs for a two-step action plus a flag
	 * indicating whether at least one matching action has an empty target
	 * (the attack-into-no-defenders case from README §8).
	 */
	getValidTargets(action: ValidAction): { targets: string[]; allowsNoDefender: boolean } {
		const mapping = TWO_STEP_ACTIONS[action.action];
		if (!mapping) return { targets: [], allowsNoDefender: false };

		const sourceId = action[mapping.source] as string;
		if (!sourceId) return { targets: [], allowsNoDefender: false };

		const targets = new Set<string>();
		let allowsNoDefender = false;
		for (const a of this._validActions) {
			if (a.action !== action.action || a[mapping.source] !== sourceId) continue;
			const target = a[mapping.target] as string;
			if (target) targets.add(target);
			else if (action.action === 'attack') allowsNoDefender = true;
		}
		return { targets: [...targets], allowsNoDefender };
	}

	/**
	 * Returns the distinct attack IDs available for a given attacker.
	 * Used by the AttackPicker UI to know whether to prompt.
	 */
	getAttackIdsForAttacker(attackerId: string): number[] {
		const ids = new Set<number>();
		for (const a of this._validActions) {
			if (a.action !== 'attack') continue;
			if (a.attacker_id !== attackerId) continue;
			const aid = a.attack_id;
			if (typeof aid === 'number') ids.add(aid);
		}
		return [...ids];
	}

	/**
	 * Find the attack action for a given attacker / attack_id / optional target.
	 * Pass an empty target to look for a no-defender attack.
	 */
	findAttackAction(attackerId: string, attackId: number, targetId: string): ValidAction | undefined {
		return this._validActions.find(a =>
			a.action === 'attack'
			&& a.attacker_id === attackerId
			&& a.attack_id === attackId
			&& (a.target_card_id ?? '') === targetId,
		);
	}

	// ── Action categories ───────────────────────────────────────────────

	canPass(): boolean {
		return this.getPassAction() !== undefined;
	}

	canConcede(): boolean {
		return this.getConcedeAction() !== undefined;
	}

	getPassAction(): ValidAction | undefined {
		return this._validActions.find(a => a.action === 'pass');
	}

	getConcedeAction(): ValidAction | undefined {
		return this._validActions.find(a => a.action === 'concede');
	}

	// ── Action execution ────────────────────────────────────────────────

	execute(action: ValidAction): void {
		this._connection.sendAction(this._toActionData(action));
	}

	// ── Private ─────────────────────────────────────────────────────────

	private _toActionData(action: ValidAction): ActionData {
		const params: Record<string, unknown> = {};
		for (const [key, value] of Object.entries(action)) {
			if (!STRIP_FIELDS.has(key)) params[key] = value;
		}
		return { action_type: action.action, ...params };
	}

	private _referencesCard(action: ValidAction, instanceId: string): boolean {
		if (NON_CARD_ACTIONS.has(action.action)) return false;

		for (const field of SOURCE_CARD_FIELDS) {
			if (action[field] === instanceId) return true;
		}

		if (Array.isArray(action.instance_ids)
			&& (action.instance_ids as string[]).includes(instanceId)) {
			return true;
		}

		if (Array.isArray(action.swaps)) {
			for (const pair of action.swaps as [string, string][]) {
				if (pair[0] === instanceId || pair[1] === instanceId) return true;
			}
		}

		return false;
	}

	private _collectSourceIds(action: ValidAction, ids: Set<string>): void {
		for (const field of SOURCE_CARD_FIELDS) {
			const value = action[field];
			if (typeof value === 'string' && value) ids.add(value);
		}

		if (Array.isArray(action.instance_ids)) {
			for (const id of action.instance_ids as string[]) {
				if (id) ids.add(id);
			}
		}

		if (Array.isArray(action.swaps)) {
			for (const [suppId, atkId] of action.swaps as [string, string][]) {
				if (suppId) ids.add(suppId);
				if (atkId) ids.add(atkId);
			}
		}
	}
}
