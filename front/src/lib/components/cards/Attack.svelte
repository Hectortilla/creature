<script lang="ts">
    import type { Attack } from '$lib/types';
	import { formatHandle } from '$lib/utils/formatHandle';

    // Components
    import NarrativeText from '$lib/components/NarrativeText.svelte';

    // Icons
    import diceRollsIcon from "$lib/icons/dice-rolls.svg?raw";
    import physical from "$lib/icons/physical-type.svg?raw";
    import magical from "$lib/icons/magical-type.svg?raw";

    // Tipado de props
    type IconName =
        string | "physical" | "magical";

    interface PageProps {
        data: Attack;
        key: number;
        allowLink?: boolean;
        showDescription?: boolean;
    }

    let {
        data,
        key,
        allowLink = true,
        showDescription = true
    }: PageProps = $props();

    // Mapa de iconos
    const iconType: Record<IconName, string> = {
        physical,
        magical
    };

</script>

<a
    href={`/attacks/${data.code}`}
    aria-label={`Ver ataque ${data.name}`}
    class={`card-attack-container theme-${formatHandle(data.element.label)}`}
    class:no-link={!allowLink}
>
    <div class="info">
        <p class="name">{data.name}</p>
        {#if data && data.dice_rolls > 0 && data.dice_rolls}
            <div class="item">
                <p>{data.dice_rolls}</p>
                <div class="icon">{@html diceRollsIcon}</div>
            </div>
        {/if}
        <div class="item">
            <p>{data.damage}</p>
            <div class="icon">{@html iconType[data.type]}</div>
        </div>
        <div class="forces">
            {#if data.necessary_force!== null && data.necessary_force.length > 0}
                {#each data.necessary_force as force}
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
        <img
            class="element"
            src={data.element.icon} alt={data.element.label}
            style="--color-element:#{data.element.color}"
        />
    </div>
    {#if data.effect}
        <div class="effect-wrapper">
            <p class="effect">Efecto</p>
            <NarrativeText text={data.effect}/>
        </div>
    {/if}
    {#if showDescription}
        <div class="description">
            <NarrativeText text={data.description}/>
        </div>
    {/if}
</a>

<style lang="scss">
    @use "$lib/styles/abstracts/variables" as variables;
    @use "$lib/styles/abstracts/mixins" as mixins;
	@use "$lib/styles/abstracts/functions" as functions;

    .card-attack-container {
        width: 100%;
        height: 100%;
        border-radius: functions.rem(16);
        padding: functions.rem(16);
        background-color: var(--color-card-background);
        box-shadow:
            0 functions.rem(-2) functions.rem(4) functions.rem(-2) transparent inset,
            0 functions.rem(2) functions.rem(6) functions.rem(1) transparent inset;
        overflow: hidden;

        @include mixins.displayFlex(column, 16, flex-start, flex-start, nowrap);
        @include mixins.transition;

        &:hover {
            box-shadow:
                0 functions.rem(0) functions.rem(4) functions.rem(-2) var(--color-input-button-light-top) inset,
                0 functions.rem(0) functions.rem(2) functions.rem(-2) var(--color-input-button-light-bottom) inset;
        }

        &.no-link {
            cursor: default;
            pointer-events: none;
        }

        .info {
            width: 100%;
            @include mixins.displayFlex(row, 16, flex-start, center, wrap);

            p.name {
                flex: 1;
                font-size: functions.rem(22);
                font-family: variables.$font-title;
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
                filter: drop-shadow(0 0 functions.rem(20) var(--color-element));
            }
        }

        .description {
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
    }

</style>