<script lang="ts">
	import type { Creature, Element } from '$lib/types';
	import { hoveredCard } from '$lib/stores/hoveredCard';
	import CardStaticDetails from '$lib/components/cards/CardStaticDetails.svelte';

	interface Props {
		cards: Creature[];
		elements: Element[];
	}

	let { cards, elements }: Props = $props();

	const cardsById = $derived(new Map(cards.map((c) => [c.id, c])));
	const payload = $derived($hoveredCard);
	const creature = $derived(payload ? cardsById.get(payload.cardId) ?? null : null);
</script>

<div class="hovered-card-overlay" class:visible={!!creature}>
	{#if creature && payload}
		<div class="panel">
			<CardStaticDetails
				card={creature}
				{elements}
				ingame={payload.ingame}
				allowLinks={false}
			/>
		</div>
	{/if}
</div>

<style lang="scss">
	@use '$lib/styles/abstracts/functions' as functions;

	.hovered-card-overlay {
		position: absolute;
		top: functions.rem(20);
		right: functions.rem(20);
		width: min(90vw, functions.rem(420));
		max-height: calc(100% - #{functions.rem(40)});
		overflow-y: auto;
		pointer-events: none;
		z-index: 10;
		opacity: 0;
		transition: opacity 0.15s ease;

		&.visible {
			opacity: 1;
		}

		// Hide scrollbar but keep scroll behaviour
		scrollbar-width: thin;
		&::-webkit-scrollbar { width: functions.rem(4); }
		&::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: functions.rem(2); }
	}

	.panel {
		background-color: var(--color-card-background, rgba(15, 10, 40, 0.85));
		backdrop-filter: blur(8px);
		border-radius: functions.rem(12);
		padding: functions.rem(20);
		box-shadow: 0 functions.rem(8) functions.rem(24) rgba(0, 0, 0, 0.3);

		display: flex;
		flex-direction: column;
		gap: functions.rem(20);
	}
</style>
