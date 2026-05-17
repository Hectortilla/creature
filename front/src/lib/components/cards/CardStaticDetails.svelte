<script lang="ts">
	import type { Creature, Element, Attack } from '$lib/types';
	import type { IngameCardState } from '$lib/stores/hoveredCard';
	import { formatHandle } from '$lib/utils/formatHandle';

	// Components
	import Icon from '$lib/components/creature/Icon.svelte';
	import Divider from '$lib/components/Divider.svelte';
	import CardAttack from '$lib/components/cards/Attack.svelte';
	import CardAbility from '$lib/components/cards/Ability.svelte';
	import CardAssociation from '$lib/components/cards/Association.svelte';
	import NarrativeText from '$lib/components/NarrativeText.svelte';
	import IngameDetails from '$lib/components/cards/IngameDetails.svelte';

	// Icons
	import healthIcon from '$lib/icons/health.svg?raw';
	import physicalDefenceIcon from '$lib/icons/physical-type.svg?raw';
	import magicDefenceIcon from '$lib/icons/magical-type.svg?raw';

	interface Props {
		card: Creature;
		elements: Element[];
		ingame?: IngameCardState;
		allowLinks?: boolean;
	}

	let { card, elements, ingame, allowLinks = true }: Props = $props();

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
</style>
