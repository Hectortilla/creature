<script lang="ts">
	import type { ActionData } from '$lib/api/types.gen';
	import { ACTION_TYPE_CONFIGS, getAllActionTypes, type ActionTypeConfig, type ActionFieldConfig } from '$lib/utils/actionFields';

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
		type: 'text' | 'number' | 'select' | 'multiselect' | 'json';
		required?: boolean;
		options?: Array<{ value: string; label: string }>;
		placeholder?: string;
		description?: string;
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

	// Convert ActionTypeConfig to ActionCard format
	function configToCard(config: ActionTypeConfig): Omit<ActionCard, 'enabled' | 'validAction'> {
		return {
			type: config.type,
			label: config.label,
			description: config.description,
			fields: config.fields.map((field) => ({
				name: field.name,
				label: field.label,
				type: field.type,
				required: field.required,
				placeholder: field.placeholder || (typeof field.example === 'string' ? field.example : undefined),
				description: field.description
			}))
		};
	}

	// Generate action definitions from the config
	const actionDefinitions: Record<string, Omit<ActionCard, 'enabled' | 'validAction'>> = Object.fromEntries(
		Object.values(ACTION_TYPE_CONFIGS).map((config) => [config.type, configToCard(config)])
	);

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
				} else if (field.type === 'json' || field.name === 'swaps') {
					// Parse JSON fields
					try {
						const parsed = JSON.parse(value);
						if (field.name === 'swaps') {
							data.swaps = parsed;
						} else {
							// For other JSON fields, assign directly
							(data as any)[field.name] = parsed;
						}
					} catch {
						console.error(`Invalid JSON for field ${field.name}`);
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
							{:else if field.type === 'json'}
								<textarea
									id="{card.type}-{field.name}"
									name={field.name}
									value={getFormValue(card.type, field.name)}
									oninput={(e) => setFormValue(card.type, field.name, (e.target as HTMLTextAreaElement).value)}
									placeholder={field.placeholder}
									required={field.required}
									disabled={!card.enabled}
									rows="3"
									style="font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 0.85rem;"
								/>
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
							{#if field.description}
								<small class="field-description">{field.description}</small>
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
	.form-field select:disabled,
	.form-field textarea:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.form-field textarea {
		width: 100%;
		padding: 0.5rem;
		background: #0d1117;
		border: 1px solid #30363d;
		border-radius: 4px;
		color: #c9d1d9;
		font-family: inherit;
		font-size: 0.85rem;
		resize: vertical;
	}

	.form-field textarea:focus {
		outline: none;
		border-color: #58a6ff;
		box-shadow: 0 0 0 2px rgba(88, 166, 255, 0.15);
	}

	.field-description {
		display: block;
		font-size: 0.75rem;
		color: #8b949e;
		margin-top: 0.25rem;
		font-style: italic;
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

