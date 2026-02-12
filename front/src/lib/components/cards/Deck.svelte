<script lang="ts">
    import { onMount } from "svelte";

    // Types
    import type { CardReadWithRelations } from "$lib/types";

    // Components
    import StylishedText from "$lib/components/StylishedText.svelte";
	import SelectorMark from "$lib/components/SelectorMark.svelte";
    import Card360 from "$lib/components/creature/Card360.svelte";

    interface Props {
        index?: number;
        text: string;
        cards?: CardReadWithRelations[];
        link?: string;
        onClick?: () => void;
        deleteDeck?: () => void;
        copyDeck?: () => void;
    }

    let {
        index = 0,
        text = "My Cards",
        cards = [],
        link = "/my-collection/cards",
        onClick,
        deleteDeck,
        copyDeck,
    }: Props = $props();

    const CARDS_TO_SHOW = 4;
    let isLoaded = $state(false);

    onMount(() => {
        // Staggered animation effect
        setTimeout(() => {
            isLoaded = true;
        }, (index + 1) * 100);
    });
</script>

<div
    class="deck-card"
    class:is-loaded={isLoaded}
>
    <svelte:element
        class="element-wrapper"
        class:is-loaded={isLoaded}
        this={link ? "a" : "button"}
        href={link}
        aria-label={text}
        role="button"
        tabindex="0"
        onclick={onClick}
    >
        <div class="selector-mark-container">
            <SelectorMark size={30} />
        </div>
        <div class="image-wrapper">
            <div style="opacity:0; z-index:-1">
                <Card360
                    data={cards[0]}
                    key={cards[0].id}
                    containerPos={0}
                    allowLink={false}
                    allowHoverEffect={false}
                    showInfo={false}
                />
            </div>
            
            {#each cards.slice(0, CARDS_TO_SHOW) as card, i}
                <div
                    class="card"
                    style={`--index: ${i * -1}; --rotate-index: ${i - Math.floor(CARDS_TO_SHOW / 2)}`}
                >
                    <Card360
                        data={card}
                        key={card.id}
                        containerPos={i}
                        allowLink={false}
                        allowHoverEffect={false}
                        showInfo={false}
                    />
                </div>
            {/each}  
        </div>
        <div class="text-wrapper">
            <StylishedText text={text} fontSize={40} />
        </div>
    </svelte:element>
    <button onclick={deleteDeck}>Delete</button>
    <button onclick={copyDeck}>Copy</button>
</div>

<style lang="scss">
    @use "../../styles/abstracts/variables" as variables;
    @use "../../styles/abstracts/mixins" as mixins;
	@use "../../styles/abstracts/functions" as functions;

    .deck-card {
        position: relative;
        width: 100%;
        max-width: functions.rem(340);
        min-width: functions.rem(300);
        opacity: 0;
        cursor: pointer;
        user-select: none;

        @include mixins.transition(.6s);
        @include mixins.displayFlex(column, 10, center, center, nowrap);

        .element-wrapper {
            width: 100%;
            height: auto;
            cursor: pointer;
            user-select: none;

            @include mixins.displayFlex(column, 30, center, center, nowrap);
        }

        .selector-mark-container {
            position: absolute;
            top: functions.rem(-40);
            left: 50%;
            transform: translateX(-50%) translateY(-50%);
            z-index: 1;
            opacity: 0;
            pointer-events: none;

            @include mixins.transition(.3s);
        }

        .image-wrapper {
            position: relative;
            width: calc(100% - functions.rem(20));
            height: auto;
            transform: scale(.9);
            //overflow: hidden;

            .card {
                perspective: 1000px;
                position: absolute;
                top: 0;
                left: 0;
                z-index: var(--index);
                transform: rotate(0);
                transform-origin: bottom center;
                pointer-events: none;

                @include mixins.transition(.4s);
            }
        }

        .text-wrapper {
            width: 100%;
            text-align: center;
            transform: translateY(functions.rem(20));
            opacity: 0;

            @include mixins.transition(.6s);
            @include mixins.displayFlex(column, 0, center, center, nowrap);
        }

        &.is-loaded {
            opacity: 1;

            .image-wrapper {
                .card {
                    opacity: 1;
                    transform: rotate(calc(var(--rotate-index) * 4deg));
                }
            }

            .text-wrapper {
                transform: translateY(functions.rem(0));
                opacity: 1;
            }
        }

        &:hover,
        &:focus {
            outline: none;

            .selector-mark-container {
                opacity: 1;
                transform: translateX(-50%) translateY(0);
            }

            .image-wrapper {
                .card {
                    transform: rotate(calc(var(--rotate-index) * 8deg));                }
            }
        }
    }
</style>