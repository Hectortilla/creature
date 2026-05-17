<script lang="ts">
	import { onDestroy } from 'svelte';
	import type { Creature, Element } from '$lib/types';
	import { hoveredCard, type HoveredCardPayload } from '$lib/stores/hoveredCard';
	import CardStaticDetails from '$lib/components/cards/CardStaticDetails.svelte';

	interface Props {
		cards: Creature[];
		elements: Element[];
	}

	let { cards, elements }: Props = $props();

	const HIDE_DELAY_MS = 600;

	const cardsById = $derived(new Map(cards.map((c) => [c.id, c])));

	let displayed = $state<HoveredCardPayload | null>(null);
	let fading = $state(false);
	let hideTimer: ReturnType<typeof setTimeout> | null = null;

	function cancelHide() {
		if (hideTimer !== null) {
			clearTimeout(hideTimer);
			hideTimer = null;
		}
		fading = false;
	}

	function scheduleHide() {
		cancelHide();
		fading = true;
		hideTimer = setTimeout(() => {
			displayed = null;
			fading = false;
			hideTimer = null;
		}, HIDE_DELAY_MS);
	}

	// React to Babylon's hover truth: show immediately when something is hovered;
	// schedule a delayed hide when nothing is — the panel's own mouseenter cancels
	// it so the user can travel from the card to the panel to scroll.
	$effect(() => {
		const incoming = $hoveredCard;
		if (incoming) {
			cancelHide();
			displayed = incoming;
		} else {
			scheduleHide();
		}
	});

	function onPanelEnter() {
		cancelHide();
	}

	function onPanelLeave() {
		// Re-evaluate against the store: if the user is no longer hovering a card,
		// start the hide countdown. If they returned to a card while inside the
		// panel, the store will keep the overlay alive on its own.
		if (!$hoveredCard) scheduleHide();
	}

	const creature = $derived(displayed ? (cardsById.get(displayed.cardId) ?? null) : null);

	onDestroy(cancelHide);
</script>

<div
	class="hovered-card-overlay"
	class:visible={!!creature}
	class:fading
	style="--hide-delay: {HIDE_DELAY_MS}ms"
>
	{#if creature && displayed}
		<div
			class="panel"
			onmouseenter={onPanelEnter}
			onmouseleave={onPanelLeave}
			role="complementary"
		>
			<CardStaticDetails
				card={creature}
				{elements}
				ingame={displayed.ingame}
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
		pointer-events: none; // empty area stays click-through to the canvas
		z-index: 10;
		opacity: 0;
		// Default transition handles appear + snap-back-from-fade
		transition: opacity 140ms ease-out;

		display: flex;
		flex-direction: column;
		align-items: flex-end;

		&.visible {
			opacity: 1;
		}

		&.visible.fading {
			opacity: 0;
			// Slow, deliberate fade so the user sees it leaving and can rescue it
			transition: opacity var(--hide-delay, 600ms) ease-in;
		}
	}

	.panel {
		pointer-events: auto; // re-enable so we receive wheel + enter/leave
		max-height: 100%;
		overflow-y: auto;
		overscroll-behavior: contain; // don't bubble wheel back to the page

		background-color: var(--color-card-background, rgba(15, 10, 40, 0.85));
		backdrop-filter: blur(8px);
		border-radius: functions.rem(12);
		padding: functions.rem(20);
		box-shadow: 0 functions.rem(8) functions.rem(24) rgba(0, 0, 0, 0.3);

		display: flex;
		flex-direction: column;
		gap: functions.rem(20);

		scrollbar-width: thin;
		&::-webkit-scrollbar { width: functions.rem(4); }
		&::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: functions.rem(2); }
	}
</style>
