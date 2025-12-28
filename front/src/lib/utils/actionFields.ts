/**
 * Action field mappings
 * 
 * Maps action types to their required and optional fields.
 * This is derived from the backend Action classes.
 */

export interface ActionFieldConfig {
	name: string;
	label: string;
	type: 'text' | 'number' | 'select' | 'multiselect' | 'json';
	required: boolean;
	description?: string;
	example?: string | number | string[];
	placeholder?: string;
}

export interface ActionTypeConfig {
	type: string;
	label: string;
	description: string;
	fields: ActionFieldConfig[];
}

/**
 * Mapping of action types to their field configurations
 * Based on the backend Action classes in back/app/game/actions.py
 */
export const ACTION_TYPE_CONFIGS: Record<string, ActionTypeConfig> = {
	draw: {
		type: 'draw',
		label: 'Draw Cards',
		description: 'Draw cards from your deck',
		fields: [
			{
				name: 'count',
				label: 'Count',
				type: 'number',
				required: true,
				description: 'Number of cards to draw',
				example: 1,
				placeholder: '1'
			}
		]
	},
	play_card: {
		type: 'play_card',
		label: 'Play Card',
		description: 'Play a card from hand to supporting zone',
		fields: [
			{
				name: 'card_id',
				label: 'Card ID',
				type: 'text',
				required: true,
				description: 'Card instance ID',
				example: 'card_instance_123',
				placeholder: 'card_instance_id'
			}
		]
	},
	multi_play_card: {
		type: 'multi_play_card',
		label: 'Play Multiple Cards',
		description: 'Play multiple cards at once',
		fields: [
			{
				name: 'card_ids',
				label: 'Card IDs',
				type: 'text',
				required: true,
				description: 'Comma-separated list of card instance IDs',
				example: 'card_instance_123, card_instance_456',
				placeholder: 'id1, id2, id3'
			}
		]
	},
	promote: {
		type: 'promote',
		label: 'Promote Card',
		description: 'Promote a card from supporting to attacking zone',
		fields: [
			{
				name: 'card_id',
				label: 'Card ID',
				type: 'text',
				required: true,
				description: 'Card instance ID',
				example: 'card_instance_123',
				placeholder: 'card_instance_id'
			}
		]
	},
	swap: {
		type: 'swap',
		label: 'Swap Cards',
		description: 'Swap a supporting card with an attacking card',
		fields: [
			{
				name: 'supporting_card_id',
				label: 'Supporting Card ID',
				type: 'text',
				required: true,
				description: 'Supporting card instance ID',
				example: 'card_instance_123',
				placeholder: 'supporting_card_id'
			},
			{
				name: 'attacking_card_id',
				label: 'Attacking Card ID',
				type: 'text',
				required: true,
				description: 'Attacking card instance ID',
				example: 'card_instance_456',
				placeholder: 'attacking_card_id'
			}
		]
	},
	multi_swap: {
		type: 'multi_swap',
		label: 'Multiple Swaps',
		description: 'Perform multiple swaps at once',
		fields: [
			{
				name: 'swaps',
				label: 'Swaps',
				type: 'json',
				required: true,
				description: 'JSON array of swap pairs',
				example: '[{"supporting_card_id": "id1", "attacking_card_id": "id2"}]',
				placeholder: '[{"supporting_card_id": "id1", "attacking_card_id": "id2"}]'
			}
		]
	},
	associate: {
		type: 'associate',
		label: 'Associate Card',
		description: 'Associate a card with an active creature',
		fields: [
			{
				name: 'association_card_id',
				label: 'Association Card ID',
				type: 'text',
				required: true,
				description: 'Association card instance ID',
				example: 'card_instance_123',
				placeholder: 'association_card_id'
			},
			{
				name: 'target_id',
				label: 'Target Card ID',
				type: 'text',
				required: true,
				description: 'Target card instance ID',
				example: 'card_instance_789',
				placeholder: 'target_card_id'
			}
		]
	},
	evolve: {
		type: 'evolve',
		label: 'Evolve Card',
		description: 'Evolve a creature with an evolution card',
		fields: [
			{
				name: 'evolution_card_id',
				label: 'Evolution Card ID',
				type: 'text',
				required: true,
				description: 'Evolution card instance ID',
				example: 'card_instance_123',
				placeholder: 'evolution_card_id'
			},
			{
				name: 'target_id',
				label: 'Target Card ID',
				type: 'text',
				required: true,
				description: 'Target card instance ID',
				example: 'card_instance_789',
				placeholder: 'target_card_id'
			}
		]
	},
	attack: {
		type: 'attack',
		label: 'Attack',
		description: 'Attack with a creature',
		fields: [
			{
				name: 'attacker_id',
				label: 'Attacker Card ID',
				type: 'text',
				required: true,
				description: 'Attacker card instance ID',
				example: 'card_instance_123',
				placeholder: 'attacker_id'
			},
			{
				name: 'attack_id',
				label: 'Attack ID',
				type: 'text',
				required: true,
				description: 'Attack ID to use',
				example: '1',
				placeholder: 'attack_id'
			},
			{
				name: 'target_id',
				label: 'Target Card ID',
				type: 'text',
				required: false,
				description: 'Target card instance ID (empty if no defenders)',
				example: 'card_instance_789',
				placeholder: 'target_id or empty'
			}
		]
	},
	force_defend: {
		type: 'force_defend',
		label: 'Force Defend',
		description: 'Move a supporting creature to defend',
		fields: [
			{
				name: 'card_id',
				label: 'Card ID',
				type: 'text',
				required: true,
				description: 'Card instance ID',
				example: 'card_instance_123',
				placeholder: 'card_instance_id'
			}
		]
	},
	pass: {
		type: 'pass',
		label: 'Pass Phase',
		description: 'Pass/end the current phase',
		fields: []
	},
	concede: {
		type: 'concede',
		label: 'Concede',
		description: 'Concede the game',
		fields: []
	}
};

/**
 * Get all known action types
 */
export function getAllActionTypes(): string[] {
	return Object.keys(ACTION_TYPE_CONFIGS);
}

/**
 * Get configuration for a specific action type
 */
export function getActionConfig(actionType: string): ActionTypeConfig | undefined {
	return ACTION_TYPE_CONFIGS[actionType];
}

/**
 * Get fields for a specific action type
 */
export function getActionFields(actionType: string): ActionFieldConfig[] {
	return ACTION_TYPE_CONFIGS[actionType]?.fields ?? [];
}

