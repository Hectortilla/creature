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

	// Drag state — position persists across hovers as long as the overlay is mounted.
	let panelEl = $state<HTMLDivElement>();
	let isDragging = $state(false);
	let isOverPanel = $state(false);
	let dragOffset = $state({ x: 0, y: 0 });
	let dragStart = { px: 0, py: 0, ox: 0, oy: 0 };

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
	// schedule a delayed hide when nothing is — unless the user is over the panel
	// or actively dragging it.
	$effect(() => {
		const incoming = $hoveredCard;
		if (incoming) {
			cancelHide();
			displayed = incoming;
		} else if (!isOverPanel && !isDragging) {
			scheduleHide();
		}
	});

	function onPanelEnter() {
		isOverPanel = true;
		cancelHide();
	}

	function onPanelLeave() {
		isOverPanel = false;
		if (!isDragging && !$hoveredCard) scheduleHide();
	}

	function onPanelPointerDown(e: PointerEvent) {
		if (!panelEl || e.button !== 0) return;
		isDragging = true;
		dragStart = { px: e.clientX, py: e.clientY, ox: dragOffset.x, oy: dragOffset.y };
		panelEl.setPointerCapture(e.pointerId);
		cancelHide();
	}

	function onPanelPointerMove(e: PointerEvent) {
		if (!isDragging) return;
		dragOffset = {
			x: dragStart.ox + (e.clientX - dragStart.px),
			y: dragStart.oy + (e.clientY - dragStart.py)
		};
	}

	function onPanelPointerUp(e: PointerEvent) {
		if (!isDragging) return;
		isDragging = false;
		panelEl?.releasePointerCapture(e.pointerId);
		if (!isOverPanel && !$hoveredCard) scheduleHide();
	}

	const creature = $derived(displayed ? (cardsById.get(displayed.cardId) ?? null) : null);
	const variants = $derived(
		creature ? cards.filter((c) => c.handle && c.handle === creature.handle) : []
	);

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
			bind:this={panelEl}
			class="panel"
			class:dragging={isDragging}
			style="transform: translate({dragOffset.x}px, {dragOffset.y}px) scale(0.85);"
			onmouseenter={onPanelEnter}
			onmouseleave={onPanelLeave}
			onpointerdown={onPanelPointerDown}
			onpointermove={onPanelPointerMove}
			onpointerup={onPanelPointerUp}
			onpointercancel={onPanelPointerUp}
			role="complementary"
		>
			<CardStaticDetails
				card={creature}
				{elements}
				{variants}
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
		width: min(90vw, functions.rem(360));
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
		touch-action: none; // prevent the browser from scrolling on pointer drag

		// Scale shrinks the panel around its anchor (top-right). The drag
		// translation is applied first in the transform string so 1 cursor px
		// = 1 panel px regardless of scale.
		transform-origin: top right;
		// Translate before scale matters: see component for ordering rationale.
		will-change: transform;
		cursor: grab;
		user-select: none;

		background-color: var(--color-card-background, rgba(15, 10, 40, 0.85));
		backdrop-filter: blur(8px);
		border-radius: functions.rem(12);
		padding: functions.rem(14);
		box-shadow: 0 functions.rem(8) functions.rem(24) rgba(0, 0, 0, 0.3);

		display: flex;
		flex-direction: column;
		gap: functions.rem(14);

		scrollbar-width: thin;
		&::-webkit-scrollbar { width: functions.rem(4); }
		&::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: functions.rem(2); }

		&.dragging {
			cursor: grabbing;
			transition: none;
		}
	}
</style>
