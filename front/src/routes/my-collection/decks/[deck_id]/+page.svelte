<script lang="ts">
    import type { PageProps } from "./$types";
    import { onMount } from "svelte";
    import { fade } from "svelte/transition";

    // Components
    import Card360 from "$lib/components/creature/Card360.svelte";
    import HorizontalScroll from "$lib/components/HorizontalScroll.svelte";
    import StylishedText from "$lib/components/StylishedText.svelte";
    import IconButton from "$lib/components/buttons/IconButton.svelte";

    // Icons
    import Arrow from "$lib/assets/icons/arrow.svg?raw";

    let { data }: PageProps = $props();
    $inspect(data);

    let deck_title = $derived(Array.isArray(data?.deck) ? null : data?.deck?.name);
    let cards = $derived(Array.isArray(data?.deck) ? null : data?.deck?.cards);
    let cardsAreLoaded = $state(false);
    let displayView = $state<'scroll' | 'grid'>('scroll');
    let scrollVelocity = $state(0);

    function onChangeDisplayView() {
        const changeTo = displayView === 'grid' ? 'scroll' : 'grid';
        displayView = changeTo;
    }

    onMount(() => {
        cardsAreLoaded = true;
    });

</script>

<div class="deck-container variables">
    {#if deck_title}
        <div class="info" class:is-loaded={cardsAreLoaded}>
            <div class="icon-pos">
                <IconButton
                    rotateIcon={90}
                    link="/my-collection/decks"
                    ariaLabel="Back to Decks"
                >
                    {@html Arrow}
                </IconButton>
            </div>
            <StylishedText text={deck_title} fontSize={46} />
            <p>{cards?.length} Cards</p>
            <button onclick={onChangeDisplayView}>Change display view</button>
        </div>
    {/if}
    {#if displayView === 'scroll'}
        <div style="width: 100%">
            <HorizontalScroll
                gap={20}
                margin={42}
                top={0}
                height={320}
                smoothFactor={1}
                bind:scrollVelocity
            >
                {#each cards as card,i}
                    <div
                        class="card-item"
                        class:is-loaded={cardsAreLoaded}
                        style={`
                            --index:${i + 1};
                            --index-reverse:${cards ? cards?.length - i : i};
                            --rotate-on-scroll:${Math.max(-45, Math.min(45, scrollVelocity))}deg;
                        `}
                    >
                        <div class="rotate-on-scroll">
                            <Card360
                                data={card}
                                key={i}
                                role="button"
                                ariaLabel="test"
                            />
                        </div>
                    </div>
                {/each}
            </HorizontalScroll>
        </div>
    {:else}
        <div class="display-grid">
            {#each cards as card,i}
                <div
                    class="card-item"
                    class:is-loaded={cardsAreLoaded}
                    style={`--index:${i + 1}; --index-reverse:${cards ? cards?.length - i : i}`}
                >
                    <Card360
                        data={card}
                        key={i}
                        role="div"
                    />
                </div>
            {/each}
        </div>
    {/if}
</div>

<style lang="scss">
    @use "../../../../lib/styles/abstracts/variables" as variables;
	@use "../../../../lib/styles/abstracts/mixins" as mixins;
	@use "../../../../lib/styles/abstracts/functions" as functions;

    .variables {
		--padding: #{
			calc(functions.rem(variables.$margin-page-desktop) - functions.rem(10))
			functions.rem(variables.$margin-page-desktop)
			0
			functions.rem(variables.$margin-page-desktop)
		};
	}

    .deck-container {
        position: relative;
        width: 100%;
        min-height: 100dvh;
        height: auto;
        overflow: hidden;
        padding-top: functions.rem(160);

        @include mixins.displayFlex(column, 0, flex-start, flex-start, nowrap);

        .info {
            padding: var(--padding);
            opacity: 0;

            transform: translateY(calc(20%));

            @include mixins.displayFlex(row, 20, flex-start, center, nowrap);
            @include mixins.transition(.6s);

            &.is-loaded {
                transform: translateY(0);
                opacity: 1;
            }

            .icon-pos {
                height: 100%;
                padding-bottom: functions.rem(12);
                @include mixins.displayFlex(row, 0, center, center, nowrap);
            }

            p {
                padding-top: functions.rem(6);
                font-size: functions.rem(18);
            }
        }

        .card-item {
            flex: 1;
            max-width: functions.rem(180);
            // max-width: functions.rem(300);
            opacity: 0;
            perspective: 1000px;

            transform: translateY(20%) rotate3d(1, 1, 0, 45deg);

            @include mixins.transition(.6s, all, calc(.08s * var(--index)));

            &.is-loaded {
                transform: translateY(0) rotate3d(0, 0, 0, 0);
                opacity: 1;
            }

            .rotate-on-scroll {
                perspective: 1000px;
                transform: rotateY(var(--rotate-on-scroll));
            }
        }

        .display-grid {
            display: grid;
            width: 100%;
            grid-template-columns: repeat(8, 1fr);
            gap: functions.rem(20);
            padding: var(--padding);

            .card-item {
                width: 100%;
                max-width: none;
                height: auto;
            }
        }
    }
</style>