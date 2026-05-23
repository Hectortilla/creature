<script lang="ts">
	import { onMount } from 'svelte';
	import type { Creature, Element, Attack } from '$lib/types';
	import type { IngameCardState } from '$lib/stores/babylon/hoveredCard';
	import { formatHandle } from '$lib/utils/formatHandle';

	// Components
	import CreatureCard360 from '$lib/components/creature/Card360.svelte';
	import Icon from '$lib/components/creature/Icon.svelte';
	import Divider from '$lib/components/Divider.svelte';
	import CardAttack from '$lib/components/cards/Attack.svelte';
	import CardAbility from '$lib/components/cards/Ability.svelte';
	import CardAssociation from '$lib/components/cards/Association.svelte';
	import NarrativeText from '$lib/components/NarrativeText.svelte';
	import IngameDetails from '$lib/components/cards/IngameDetails.svelte';

	// Icons
	import healthIcon from '$lib/assets/icons/health.svg?raw';
	import physicalDefenceIcon from '$lib/assets/icons/physical-type.svg?raw';
	import magicDefenceIcon from '$lib/assets/icons/magical-type.svg?raw';

	interface Props {
		card: Creature;
		elements: Element[];
		variants?: Creature[];
		ingame?: IngameCardState;
		allowLinks?: boolean;
	}

	let { card, elements, variants = [], ingame, allowLinks = true }: Props = $props();

	const forces = $derived(
		card.forces && Array.isArray(card.forces)
			? (card.forces as Array<{ value: number; elementData: { label: string } }>)
			: []
	);

	function findElement(id: number | undefined | null): Element | null {
		if (!id) return null;
		return elements?.find((e) => e.id === id) ?? null;
	}

	function attackUnaffordable(attack: Attack | null | undefined): boolean {
		if (!ingame || !attack) return false;
		return !ingame.affordableAttackIds.has(attack.id);
	}

	// Evolution chain expansion (lifted from the page so the overlay gets it too).
	function getAllEvolutionLines(root: Creature): Creature[][] {
		const getPreChains = (c: Creature): Creature[][] => {
			if (!c.is_evolution) return [[c]];
			const prev = c.is_evolution;
			const chains: Creature[][] = [];
			if (Array.isArray(prev)) {
				for (const p of prev) {
					for (const chain of getPreChains(p as Creature)) chains.push([...chain, c]);
				}
			} else {
				for (const chain of getPreChains(prev as Creature)) chains.push([...chain, c]);
			}
			return chains;
		};
		const getNextChains = (c: Creature): Creature[][] => {
			if (!c.next_evolutions || c.next_evolutions.length === 0) return [[c]];
			const chains: Creature[][] = [];
			for (const n of c.next_evolutions) {
				for (const chain of getNextChains(n as Creature)) chains.push([c, ...chain]);
			}
			return chains;
		};
		const preChains = getPreChains(root);
		const allLines: Creature[][] = [];
		for (const preChain of preChains) {
			const last = preChain[preChain.length - 1];
			for (const nextChain of getNextChains(last)) {
				allLines.push([...preChain.slice(0, -1), ...nextChain]);
			}
		}
		return allLines;
	}

	const evoLines = $derived(getAllEvolutionLines(card));
	const otherVariants = $derived(variants.filter((v) => v.code !== card.code));

	let evoContainer = $state<HTMLElement>();
	let evoContainerPos = $state(0);
	let variantsContainer = $state<HTMLElement>();
	let variantsContainerPos = $state(0);

	onMount(() => {
		evoContainerPos = evoContainer?.getBoundingClientRect().top ?? 0;
		variantsContainerPos = variantsContainer?.getBoundingClientRect().top ?? 0;
	});
</script>

<div class="pre-info">
	<div class="title">
		<h1>{card.name}</h1>
		<div class="classification">
			{#if card.type?.icon}
				<Icon name={card.type.icon} size={28} isBackground={false} />
			{/if}
			{#if card.character?.icon}
				<Icon name={card.character.icon} size={28} isBackground={false} />
			{/if}
		</div>
	</div>
	{#if card.description}
		<div class="description">
			<NarrativeText text={card.description} />
		</div>
	{/if}
	<p class="date">
		Fecha de creación: {card.created_at
			? new Intl.DateTimeFormat('es-ES', {
					day: '2-digit',
					month: 'short',
					year: 'numeric'
				}).format(new Date(card.created_at))
			: ''}
	</p>
</div>

<Divider title="Características" hasMargins={false} />
<div class="info">
	<div class="elements">
		{#if card.first_element}
			<img
				src={card.first_element.icon}
				alt={card.first_element.label}
				style="--color-element:#{card.first_element.color ?? '000000'}70"
			/>
		{/if}
		{#if card.second_element}
			<img
				src={card.second_element.icon}
				alt={card.second_element.label}
				style="--color-element:#{card.second_element.color ?? '000000'}70"
			/>
		{/if}
	</div>
	<div class="skills">
		<div class="item">
			<div class="icon">{@html healthIcon}</div>
			<p>{card.health ?? 0}</p>
		</div>
		<div class="item">
			<div class="icon">{@html physicalDefenceIcon}</div>
			<p>{card.physical_defence ?? 0}</p>
		</div>
		<div class="item">
			<div class="icon">{@html magicDefenceIcon}</div>
			<p>{card.magic_defence ?? 0}</p>
		</div>
	</div>
	{#if forces.length > 0}
		<div class="forces">
			{#each forces as force}
				<div class={`force-item theme-${formatHandle(force.elementData.label)}`}>
					<p>{force.value}</p>
				</div>
			{/each}
		</div>
	{:else}
		<p class="empty">No aporta fuerza</p>
	{/if}
</div>

<Divider title="Daño por elemento" hasMargins={false} />
<div class="info">
	<div class="element-damage-wrapper">
		{#each card.weaknesses ?? [] as weaknessId}
			{@const weakness = findElement(weaknessId)}
			{#if weakness}
				<div class="item weakness">
					<img
						src={weakness.icon}
						alt={weakness.label}
						style="--color-element:#{weakness.color ?? '000000'}70"
					/>
					<p>+5</p>
				</div>
			{/if}
		{/each}
		{#each card.strengths ?? [] as strengthId}
			{@const strength = findElement(strengthId)}
			{#if strength}
				<div class="item strength">
					<img
						src={strength.icon}
						alt={strength.label}
						style="--color-element:#{strength.color ?? '000000'}70"
					/>
					<p>-5</p>
				</div>
			{/if}
		{/each}
	</div>
</div>

{#if card.first_attack || card.second_attack}
	<Divider title="Ataques" hasMargins={false} />
	<div class="attacks-container">
		{#if card.first_attack}
			<div class="attack-slot" class:dim={attackUnaffordable(card.first_attack)}>
				<CardAttack data={card.first_attack} key={1} allowLink={allowLinks} />
			</div>
		{/if}
		{#if card.second_attack}
			<div class="attack-slot" class:dim={attackUnaffordable(card.second_attack)}>
				<CardAttack data={card.second_attack} key={2} allowLink={allowLinks} />
			</div>
		{/if}
	</div>
{/if}

{#if card.ability}
	<Divider title="Habilidad" hasMargins={false} />
	<CardAbility data={card.ability} allowLink={allowLinks} showDescription={true} />
{/if}

{#if card.association}
	<Divider title="Asociación" hasMargins={false} />
	<CardAssociation data={card.association} allowLink={allowLinks} showDescription={true} />
{/if}

{#if ingame}
	<IngameDetails state={ingame} />
{/if}

{#if evoLines.length > 0 && evoLines[0].length > 1}
	<Divider
		title={evoLines.length > 1 ? 'Líneas evolutivas' : 'Línea evolutiva'}
		hasMargins={false}
	/>
	<div class="evo-line-container" bind:this={evoContainer}>
		{#each evoLines as line, lineI}
			<div class="evo-line-wrapper">
				{#each line as item, i}
					<div class="card-item" class:selected={item.code === card.code}>
						<CreatureCard360
							data={item}
							key={lineI * 10 + i}
							showCode={item.code !== card.code}
							showInfo={false}
							showEvolutionCode={false}
							allowLink={allowLinks && item.code !== card.code}
							allowHoverEffect={item.code !== card.code}
							containerPos={evoContainerPos}
						/>
						<svg xmlns="http://www.w3.org/2000/svg" width="334" height="378" viewBox="0 0 334 378" fill="none">
							<path d="M323.111 171.679C336.445 179.377 336.445 198.622 323.111 206.32L30.6919 375.149C17.3586 382.847 0.691878 373.224 0.691879 357.828L0.691894 20.1715C0.691894 4.77545 17.3586 -4.84709 30.6919 2.85091L323.111 171.679Z" fill="currentColor" />
						</svg>
					</div>
				{/each}
			</div>
		{/each}
	</div>
{/if}

{#if otherVariants.length > 0}
	<Divider
		title={otherVariants.length > 1 ? 'Variantes' : 'Variante'}
		hasMargins={false}
	/>
	<div class="gallery-cards" bind:this={variantsContainer}>
		{#each otherVariants as variant, i}
			<CreatureCard360
				data={variant}
				key={i}
				showCode={true}
				showInfo={true}
				showEvolutionCode={true}
				allowLink={allowLinks}
				allowHoverEffect={true}
				containerPos={variantsContainerPos}
			/>
		{/each}
	</div>
{/if}

<style lang="scss">
	@use '$lib/styles/abstracts/variables' as variables;
	@use '$lib/styles/abstracts/mixins' as mixins;
	@use '$lib/styles/abstracts/functions' as functions;

	.pre-info {
		width: 100%;
		@include mixins.displayFlex(column, 12, flex-start, flex-start, wrap);

		.title {
			width: 100%;
			@include mixins.displayFlex(row, 20, space-between, center, wrap);

			h1 {
				font-family: variables.$font-title;
				font-size: functions.rem(48);
				font-weight: 400;
			}

			.classification {
				color: var(--color-foreground);
				@include mixins.displayFlex(row, 8, flex-start, flex-start, nowrap);
			}
		}

		.description {
			width: 100%;
			opacity: 0.6;
		}

		.date {
			width: 100%;
			opacity: 0.4;
			font-size: functions.rem(14);
		}
	}

	.info {
		width: 100%;
		@include mixins.displayFlex(row, 26, space-between, center, wrap);

		.elements {
			@include mixins.displayFlex(row, 6, space-between, flex-start, wrap);

			img {
				width: functions.rem(30);
				filter: drop-shadow(0 0 functions.rem(20) var(--color-element));
			}
		}

		.skills {
			flex: 1;
			@include mixins.displayFlex(row, 18, flex-start, flex-start, nowrap);

			.item {
				@include mixins.displayFlex(row, 4, flex-start, center, nowrap);

				.icon {
					width: functions.rem(20);
					height: functions.rem(20);
					margin-top: functions.rem(0);
				}

				p {
					font-family: variables.$font-number;
					font-size: functions.rem(24);
					line-height: 126%;
				}
			}
		}

		.forces {
			@include mixins.displayFlex(row, 10, flex-start, center, nowrap);

			.force-item {
				width: functions.rem(24);
				height: functions.rem(24);
				border-radius: functions.rem(4);
				border: solid 1px var(--color-forces-border);
				background-color: var(--color-force-background);
				transform: rotate(45deg);
				@include mixins.displayFlex(column, 0, center, center, nowrap);

				p {
					color: var(--color-force-foreground);
					font-family: variables.$font-number;
					font-size: functions.rem(20);
					transform: rotate(-45deg);
				}
			}
		}

		.empty {
			opacity: 0.4;
		}

		.element-damage-wrapper {
			@include mixins.displayFlex(row, 10, center, center, nowrap);

			.item {
				background-color: var(--color-pop-in-background);
				padding: functions.rem(4) functions.rem(8) functions.rem(4) functions.rem(4);
				border-radius: functions.rem(8);
				overflow: hidden;

				@include mixins.displayFlex(row, 6, center, center, nowrap);

				p {
					font-size: functions.rem(14);
				}

				&.weakness p { color: functions.color(semantic, error, 80%, 60%); }
				&.strength p { color: functions.color(semantic, success, 80%, 60%); }

				img {
					width: functions.rem(26);
					height: functions.rem(26);
					filter: drop-shadow(0 0 functions.rem(20) var(--color-element));
				}
			}
		}
	}

	.attacks-container {
		width: 100%;
		@include mixins.displayFlex(column, 12, flex-start, flex-start, nowrap);

		.attack-slot {
			width: 100%;
			transition: opacity 0.2s ease;

			&.dim {
				opacity: 0.4;
				filter: grayscale(0.5);
			}
		}
	}

	.evo-line-container {
		width: 100%;
		@include mixins.displayFlex(column, 60, flex-start, flex-start, nowrap);

		.evo-line-wrapper {
			@include mixins.displayFlex(row, 60, flex-start, center, nowrap);

			.card-item {
				perspective: 1000px;
				position: relative;
				flex: 1;
				max-width: functions.rem(160);

				&.selected {
					flex: 0.8;
					max-width: functions.rem(120);
				}

				svg {
					position: absolute;
					top: 50%;
					right: 0;
					transform: translateY(-50%) translateX(150%);
					width: functions.rem(30);
					height: functions.rem(30);
					color: var(--color-divider-bar);
					z-index: -1;
					pointer-events: none;
					fill-opacity: 0.6;
				}

				&:last-child svg {
					display: none;
				}
			}
		}
	}

	.gallery-cards {
		width: 100%;
		perspective: 1000px;
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: functions.rem(20);
	}
</style>
