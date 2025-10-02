<script lang="ts">
    import type { Attack, Creature } from "$lib/types";
	import { formatHandle } from '$lib/utils/formatHandle';
    import { changeThemeTo } from '$lib/utils/changeThemeTo';
    import { onDestroy, onMount } from 'svelte';
    import { goto } from "$app/navigation";

    // Components
    import NarrativeText from '$lib/components/NarrativeText.svelte';
    import Divider from "$lib/components/Divider.svelte";
    import Button from "$lib/components/Button.svelte";
    import Card360 from '$lib/components/creature/Card360.svelte';

    // Icons
    import diceRollsIcon from "$lib/icons/dice-rolls.svg?raw";
    import physical from "$lib/icons/physical-type.svg?raw";
    import magical from "$lib/icons/magical-type.svg?raw";

    interface PageProps {
        data: {
            params: {
                attack?: string;
            };
            attack?: Attack;
            cards_use_attack: Creature[]
        };
    }

    // Tipado de props
    type IconName = string | "physical" | "magical";

    // Mapa de iconos
    const iconType: Record<IconName, string> = {
        physical,
        magical
    };

    let { data }: PageProps = $props();
    console.log(data);

    let attack = $derived.by(() => data.attack ? data.attack : null);

    // Container card position
    let cardContainer = $state<HTMLElement>();
    let cardContainerPosition = $state(0);

    onMount (() => {
        cardContainerPosition = cardContainer?.getBoundingClientRect().top ?? 0;
    });

    $effect(() => {
        if (attack) changeThemeTo(attack.element?.label);
        else changeThemeTo("default");
    });

    const handleDeleteAttack = async () => {
        if (!attack) return;
		await fetch('/api/attacks', {
			method: 'DELETE',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ id: attack.id })
		});
        goto('/attacks');
	};

    onDestroy(() => {
        changeThemeTo("default");
    }); 

</script>
<div class="attack-container">
    {#if attack}
        <div class="attack-info">
            <div class="info">
                <h1 class="name">{attack.name}</h1>
                {#if data && attack.dice_rolls > 0 && attack.dice_rolls}
                    <div class="item">
                        <p>{attack.dice_rolls}</p>
                        <div class="icon">{@html diceRollsIcon}</div>
                    </div>
                {/if}
                <div class="item">
                    <p>{attack.damage}</p>
                    <div class="icon">{@html iconType[attack.type]}</div>
                </div>
                <div class="forces">
                    {#if attack.necessary_force !== null && attack.necessary_force.length > 0}
                        {#each attack.necessary_force as force}
                            <div class={`force-item theme-${formatHandle(force.elementData.label)}`}>
                                <p>{force.value}</p>
                            </div>
                        {/each}
                    {:else}
                        <div class="force-item zero theme-ether">
                            <p>0</p>
                        </div>
                    {/if}
                </div>
                <img class="element" src={attack.element.icon} alt={attack.element.label} />
            </div>
            <Divider title={false} hasMargins={false}/>
            <div class="element-damage-wrapper">
                {#each attack.weaknesses as weakness}
                    <div class="item weakness">
                        <img
                            src={weakness.element.icon}
                            alt={weakness.element.label}
                            style="--color-element:#{weakness.element.color}70"
                        />
                        <p>-{weakness.value}</p>
                    </div>
                {/each}
                {#each attack.strengths as strength}
                    <div class="item strength">
                        <img
                            src={strength.element.icon}
                            alt={strength.element.label}
                            style="--color-element:#{strength.element.color}70"
                        />
                        <p>+{strength.value}</p>
                    </div>
                {/each}
            </div>
            {#if attack.effect}
                <Divider title={false} hasMargins={false}/>
                <div class="effect-wrapper">
                    <p class="effect">Efecto</p>
                    <NarrativeText text={attack.effect}/>
                </div>
            {/if}
            <Divider title={false} hasMargins={false}/>
            <p class="description">
                {attack.description}
            </p>
            {#if data.cards_use_attack.length > 0}
                <Divider title={`Cartas con este ataque (${data.cards_use_attack.length})`} hasMargins={false}/>
                <div class="cards-gallery">
                    {#each data.cards_use_attack as card,i}
                        <Card360
                            data={card}
                            key={i}
                            showCode={true}
                            showInfo={true}
                            showEvolutionCode={true}
                            containerPos={cardContainerPosition}
                        />
                    {/each}
                </div>
            {/if}
            <Button type="primary" text="Borrar ataque" onClick={handleDeleteAttack} isDisabled={false} />
        </div>
    {/if}
</div>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .attack-container {
        @include mixins.displayFlex(column, 0, center, center, nowrap);
    }

    .attack-info{
        width: 100%;
        padding-top: functions.rem(60);
        max-width: functions.rem(800);

        @include mixins.displayFlex(column, 26, flex-start, flex-start, nowrap);
        @include mixins.margins;

        .info {
            width: 100%;
            @include mixins.displayFlex(row, 20, flex-start, center, wrap);

            h1.name {
                flex: 1;
                font-size: functions.rem(48);
                font-family: variables.$font-title;
                font-weight: 300;
            }

            .item {
                @include mixins.displayFlex(row, 4, flex-start, center, wrap);

                p {
                    font-size: functions.rem(22);
                    font-family: variables.$font-number;
                    line-height: 100%;
                }

                .icon {
                    width: functions.rem(20);
                    height: functions.rem(20);
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

                    &.zero p{
                        opacity: .6;
                    }

                    p {
                        color: var(--color-force-foreground);
                        font-family: variables.$font-number;
                        font-size: functions.rem(20);
                        transform: rotate(-45deg);
                    }
                }
            }

            img.element {
                width: functions.rem(30);
                height: functions.rem(30);
            }
        }

        p.description {
            opacity: .6;
        }

        .effect-wrapper {
            @include mixins.displayFlex(column, 6, flex-start, flex-start, nowrap);

            p.effect {
                background-color: var(--color-input-button-light-bottom);
                color: var(--color-text);
                font-family: variables.$font-title;
                font-size: functions.rem(14);
                padding: 0 functions.rem(4);
                border-radius: functions.rem(4);
                margin-left: functions.rem(-2);
                opacity: .6;
            }
        }

        .cards-gallery {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            perspective: 1000px;
            gap: functions.rem(20);
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

</style>