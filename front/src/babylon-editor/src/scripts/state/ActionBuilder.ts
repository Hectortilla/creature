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
	'action', 'player_id', 'description',
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
		const mapping = TWO_STEP_ACTIONS[action.action];
		if (!mapping) return [];

		const sourceId = action[mapping.source] as string;
		if (!sourceId) return [];

		const targets = new Set<string>();
		for (const a of this._validActions) {
			if (a.action !== action.action || a[mapping.source] !== sourceId) continue;
			const target = a[mapping.target] as string;
			if (target) targets.add(target);
		}
		return [...targets];
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
