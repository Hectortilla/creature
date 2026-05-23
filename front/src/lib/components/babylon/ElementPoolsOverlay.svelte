<script lang="ts">
	import type { Element } from '$lib/types';
	import { elementPools, type ElementPoolSnapshot } from '$lib/stores/babylon/elementPools';
	import Divider from '$lib/components/Divider.svelte';

	interface Props {
		elements: Element[];
	}

	let { elements }: Props = $props();

	const elementsById = $derived(new Map(elements.map((e) => [e.id, e])));

	type Entry = { element: Element; current: number; max: number };

	function entriesFor(pool: ElementPoolSnapshot, lookup: Map<number, Element>): Entry[] {
		const out: Entry[] = [];
		for (const [idStr, current] of Object.entries(pool.elements)) {
			const id = Number(idStr);
			const element = lookup.get(id);
			if (!element) continue;
			const max = pool.maxElements[idStr] ?? current;
			out.push({ element, current, max });
		}
		return out.sort((a, b) => a.element.id - b.element.id);
	}

	const myEntries = $derived(
		$elementPools ? entriesFor($elementPools.myPool, elementsById) : []
	);
	const oppEntries = $derived(
		$elementPools ? entriesFor($elementPools.oppPool, elementsById) : []
	);
</script>

{#if $elementPools}
	<div class="element-pools-overlay">
		<div class="panel">
			<Divider title="My Elements" hasMargins={false} />
			<div class="tiles">
				{#each myEntries as { element, current, max } (element.id)}
					{@const color = element.color ?? '888888'}
					<div
						class="tile"
						class:depleted={current === 0}
						style="--color-element:#{color}; --color-element-fill:#{color}22; --color-element-border:#{color}66; --color-element-badge:#{color}aa"
						title={element.label}
					>
						<img src={element.icon} alt={element.label} />
						<span class="badge">{current}/{max}</span>
					</div>
				{/each}
			</div>

			<Divider title="Opponent" hasMargins={false} />
			<div class="tiles">
				{#each oppEntries as { element, current, max } (element.id)}
					{@const color = element.color ?? '888888'}
					<div
						class="tile opponent"
						class:depleted={current === 0}
						style="--color-element:#{color}; --color-element-fill:#{color}22; --color-element-border:#{color}66; --color-element-badge:#{color}aa"
						title={element.label}
					>
						<img src={element.icon} alt={element.label} />
						<span class="badge">{current}/{max}</span>
					</div>
				{/each}
			</div>
		</div>
	</div>
{/if}

<style lang="scss">
	@use '$lib/styles/abstracts/functions' as functions;

	.element-pools-overlay {
		position: absolute;
		bottom: functions.rem(20);
		left: functions.rem(20);
		pointer-events: none;
		z-index: 10;
	}

	.panel {
		pointer-events: auto;
		background-color: var(--color-card-background, rgba(15, 10, 40, 0.85));
		backdrop-filter: blur(8px);
		border-radius: functions.rem(12);
		padding: functions.rem(12);
		box-shadow: 0 functions.rem(8) functions.rem(24) rgba(0, 0, 0, 0.3);

		display: flex;
		flex-direction: column;
		gap: functions.rem(8);

		min-width: functions.rem(200);
	}

	.tiles {
		display: flex;
		flex-wrap: wrap;
		gap: functions.rem(10);
		padding: functions.rem(4) 0;
	}

	.tile {
		position: relative;
		width: functions.rem(44);
		height: functions.rem(44);
		border-radius: functions.rem(8);
		background-color: var(--color-element-fill);
		border: 1px solid var(--color-element-border);
		display: flex;
		align-items: center;
		justify-content: center;
		transition: opacity 120ms ease-out;

		img {
			width: 70%;
			height: 70%;
			object-fit: contain;
			filter: drop-shadow(0 0 functions.rem(8) var(--color-element));
		}

		&.depleted {
			opacity: 0.35;
			filter: grayscale(0.6);
		}

		&.opponent {
			border-style: dashed;
		}
	}

	.badge {
		position: absolute;
		top: functions.rem(-6);
		right: functions.rem(-6);
		min-width: functions.rem(22);
		padding: 0 functions.rem(4);
		height: functions.rem(16);
		border-radius: functions.rem(8);
		background-color: rgba(0, 0, 0, 0.85);
		color: #ffffff;
		font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
		font-size: functions.rem(10);
		line-height: functions.rem(16);
		text-align: center;
		box-shadow: 0 0 0 1px var(--color-element-badge);
	}
</style>
