<script lang="ts">
	import type { ActionData } from '$lib/api/types.gen';

	interface ActionCard {
		type: string;
		label: string;
		description: string;
		fields: ActionField[];
		enabled: boolean;
		validAction?: ValidAction;
	}

	interface ActionField {
		name: string;
		label: string;
		type: 'text' | 'number' | 'select' | 'multiselect';
		required?: boolean;
		options?: Array<{ value: string; label: string }>;
		placeholder?: string;
	}

	interface ValidAction {
		action: string;
		player_id: string;
		[key: string]: unknown;
	}

	interface Props {
		validActions: ValidAction[];
		onSendAction: (action: ActionData) => void;
	}

	let { validActions = $bindable([]), onSendAction }: Props = $props();

	// Define all possible action types with their form fields
	const actionDefinitions: Record<string, Omit<ActionCard, 'enabled' | 'validAction'>> = {
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
					label: 'Card IDs (comma-separated)',
					type: 'text',
					required: true,
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
					placeholder: 'supporting_card_id'
				},
				{
					name: 'attacking_card_id',
					label: 'Attacking Card ID',
					type: 'text',
					required: true,
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
					label: 'Swaps (JSON array)',
					type: 'text',
					required: true,
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
					placeholder: 'association_card_id'
				},
				{
					name: 'target_id',
					label: 'Target Card ID',
					type: 'text',
					required: true,
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
					placeholder: 'evolution_card_id'
				},
				{
					name: 'target_id',
					label: 'Target Card ID',
					type: 'text',
					required: true,
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
					placeholder: 'attacker_id'
				},
				{
					name: 'attack_id',
					label: 'Attack ID',
					type: 'text',
					required: true,
					placeholder: 'attack_id'
				},
				{
					name: 'target_id',
					label: 'Target Card ID (empty if no defenders)',
					type: 'text',
					required: false,
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

	// Create action cards from definitions
	const actionCards = $derived(
		Object.values(actionDefinitions).map((def) => {
			// Find if this action type has any valid actions
			const matchingValidActions = validActions.filter((va) => va.action === def.type);
			const enabled = matchingValidActions.length > 0;
			
			// If enabled, use the first valid action as a template (for pre-filling)
			const validAction = enabled ? matchingValidActions[0] : undefined;

			return {
				...def,
				enabled,
				validAction
			} as ActionCard;
		})
	);

	// Form data for each action card - initialize with all card types
	const formData: Record<string, Record<string, string>> = $state({});

	// Initialize form data for each action
	$effect(() => {
		actionCards.forEach((card) => {
			if (!formData[card.type]) {
				formData[card.type] = {};
			}
			// Initialize all fields for this card type
			card.fields.forEach((field) => {
				if (!(field.name in formData[card.type])) {
					formData[card.type][field.name] = '';
				}
			});
			// Pre-fill from valid action if available
			if (card.validAction) {
				card.fields.forEach((field) => {
					const value = card.validAction?.[field.name];
					if (value !== undefined && !formData[card.type][field.name]) {
						if (field.type === 'multiselect' && Array.isArray(value)) {
							formData[card.type][field.name] = value.join(', ');
						} else {
							formData[card.type][field.name] = String(value);
						}
					}
				});
			}
		});
	});

	// Helper to get form data value safely (non-mutating)
	function getFormValue(cardType: string, fieldName: string): string {
		return formData[cardType]?.[fieldName] ?? '';
	}

	// Helper to set form data value
	function setFormValue(cardType: string, fieldName: string, value: string): void {
		if (!formData[cardType]) {
			formData[cardType] = {};
		}
		formData[cardType][fieldName] = value;
	}

	function handleSubmit(card: ActionCard, event: Event) {
		event.preventDefault();
		
		if (!card.enabled) return;

		// Ensure formData is initialized for this card type
		if (!formData[card.type]) {
			formData[card.type] = {};
		}

		const data: ActionData = {
			action_type: card.type
		};

		// Build action data from form
		card.fields.forEach((field) => {
			const fieldValue = formData[card.type]?.[field.name];
			const value = typeof fieldValue === 'string' ? fieldValue.trim() : '';
			
			if (field.required && !value) {
				return; // Skip if required field is empty
			}

			if (value) {
				if (field.name === 'card_ids') {
					// Parse comma-separated card IDs
					data.card_ids = value.split(',').map((id) => id.trim()).filter(Boolean);
				} else if (field.name === 'swaps') {
					// Parse JSON swaps
					try {
						data.swaps = JSON.parse(value);
					} catch {
						console.error('Invalid swaps JSON');
						return;
					}
				} else if (field.type === 'number') {
					const numValue = parseInt(value, 10);
					if (!isNaN(numValue)) {
						(data as any)[field.name] = numValue;
					}
				} else {
					(data as any)[field.name] = value;
				}
			}
		});

		onSendAction(data);
	}

	function getActionDescription(card: ActionCard): string {
		if (card.validAction && 'description' in card.validAction) {
			return String(card.validAction.description);
		}
		return card.description;
	}
</script>

<div class="action-cards-container">
	<h2>Available Actions</h2>
	<div class="action-cards-grid">
		{#each actionCards as card}
			<div class="action-card" class:enabled={card.enabled} class:disabled={!card.enabled}>
				<div class="action-card-header">
					<h3>{card.label}</h3>
					<span class="action-type-badge">{card.type}</span>
				</div>
				<p class="action-description">{getActionDescription(card)}</p>
				
				{#if card.enabled}
					<span class="enabled-badge">✓ Available</span>
				{:else}
					<span class="disabled-badge">✗ Not Available</span>
				{/if}

				<form onsubmit={(e) => handleSubmit(card, e)}>
					{#each card.fields as field}
						<div class="form-field">
							<label for="{card.type}-{field.name}">
								{field.label}
								{#if field.required}
									<span class="required">*</span>
								{/if}
							</label>
							{#if field.type === 'select' && field.options}
								<select
									id="{card.type}-{field.name}"
									name={field.name}
									value={getFormValue(card.type, field.name)}
									onchange={(e) => setFormValue(card.type, field.name, (e.target as HTMLSelectElement).value)}
									required={field.required}
									disabled={!card.enabled}
								>
									<option value="">Select...</option>
									{#each field.options as option}
										<option value={option.value}>{option.label}</option>
									{/each}
								</select>
							{:else}
								<input
									id="{card.type}-{field.name}"
									type={field.type === 'number' ? 'number' : 'text'}
									name={field.name}
									value={getFormValue(card.type, field.name)}
									oninput={(e) => setFormValue(card.type, field.name, (e.target as HTMLInputElement).value)}
									placeholder={field.placeholder}
									required={field.required}
									disabled={!card.enabled}
								/>
							{/if}
						</div>
					{/each}
					
					<button type="submit" disabled={!card.enabled} class="send-button">
						Send {card.label}
					</button>
				</form>
			</div>
		{/each}
	</div>
</div>

<style>
	.action-cards-container {
		padding: 0;
		background: transparent;
		border: none;
		margin: 0;
	}

	.action-cards-container h2 {
		display: none;
	}

	.action-cards-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 1rem;
	}

	.action-card {
		padding: 1rem;
		background: #0d1117;
		border: 2px solid #30363d;
		border-radius: 8px;
		transition: all 0.2s ease;
	}

	.action-card.enabled {
		border-color: #3fb950;
		background: rgba(63, 185, 80, 0.05);
	}

	.action-card.disabled {
		opacity: 0.6;
		border-color: #484f58;
	}

	.action-card-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 0.5rem;
	}

	.action-card-header h3 {
		margin: 0;
		font-size: 1rem;
		color: #c9d1d9;
	}

	.action-type-badge {
		font-size: 0.75rem;
		padding: 0.25rem 0.5rem;
		background: #21262d;
		border: 1px solid #30363d;
		border-radius: 4px;
		color: #8b949e;
		font-family: 'JetBrains Mono', 'Fira Code', monospace;
	}

	.action-description {
		margin: 0.5rem 0;
		font-size: 0.85rem;
		color: #8b949e;
	}

	.enabled-badge {
		display: inline-block;
		font-size: 0.75rem;
		padding: 0.25rem 0.5rem;
		background: rgba(63, 185, 80, 0.15);
		color: #3fb950;
		border-radius: 4px;
		margin-bottom: 0.75rem;
		font-weight: 600;
	}

	.disabled-badge {
		display: inline-block;
		font-size: 0.75rem;
		padding: 0.25rem 0.5rem;
		background: rgba(248, 81, 73, 0.15);
		color: #f85149;
		border-radius: 4px;
		margin-bottom: 0.75rem;
		font-weight: 600;
	}

	.form-field {
		margin-bottom: 0.75rem;
	}

	.form-field label {
		display: block;
		font-size: 0.85rem;
		color: #c9d1d9;
		margin-bottom: 0.25rem;
	}

	.form-field .required {
		color: #f85149;
	}

	.form-field input,
	.form-field select {
		width: 100%;
		padding: 0.5rem;
		background: #0d1117;
		border: 1px solid #30363d;
		border-radius: 4px;
		color: #c9d1d9;
		font-family: inherit;
		font-size: 0.85rem;
	}

	.form-field input:focus,
	.form-field select:focus {
		outline: none;
		border-color: #58a6ff;
		box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.15);
	}

	.form-field input:disabled,
	.form-field select:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.send-button {
		width: 100%;
		padding: 0.75rem;
		background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
		border: none;
		border-radius: 6px;
		color: #fff;
		font-family: inherit;
		font-size: 0.9rem;
		font-weight: 600;
		cursor: pointer;
		transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
		margin-top: 0.5rem;
	}

	.send-button:hover:not(:disabled) {
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(46, 160, 67, 0.4);
	}

	.send-button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
		background: #30363d;
	}
</style>

