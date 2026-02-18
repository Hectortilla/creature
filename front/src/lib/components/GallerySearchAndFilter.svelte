<script lang="ts">
	import { FONT_BASE_SIZE } from "$lib/constants";
	import type { Snippet } from "svelte";
    import { onMount } from "svelte";
    import { page } from '$app/state';

    // Components
    import Card360 from "$lib/components/creature/Card360.svelte";
	import path from "node:path";

    interface Props {
        cards: any;
        showSearch?: boolean;
        showFilters?: boolean;
        onClickOnCard?: (cardId:number) => void;
    }

    let {
        cards,
        showSearch = true,
        showFilters = true,
        onClickOnCard,
    }: Props = $props();

    let cardsAreLoaded = $state(false);
    let search = $state("");

    let searchCardsByName = $derived(
        cards.filter((card: any) =>
            card.name
                ?.toLowerCase()
                .includes(search.toLowerCase())
    ))

    // Force animation on appear
    $effect(() => {
        page.url.pathname;

        cardsAreLoaded = false;

        requestAnimationFrame(() => {
            cardsAreLoaded = true;
        });
    });

</script>
<div class="gallery-search-and-filter-outer variables">
    {#if showSearch || showFilters}
        <div class="search-and-filter" class:is-loaded={cardsAreLoaded}>
            {#if showSearch}
                <input type="search" placeholder="Search by name" bind:value={search}/>
            {/if}
        </div>
    {/if}
    <div class="gallery-wrapper">
        {#each searchCardsByName as card, i (card.id + '-' + i)}
            <div
                class="card-item"
                class:is-loaded={cardsAreLoaded}
                style={`
                    --index:${i + 1};
                    --index-reverse:${cards ? cards?.length - i : i};
                `}
            >
                <Card360
                    data={card}
                    key={i}
                    role="button"
                    ariaLabel="test"
                    onClick={() => onClickOnCard && onClickOnCard(card.id)}
                ></Card360>
            </div>
        {/each}
    </div>
</div>

<style lang="scss">
    @use "../styles/abstracts/variables" as variables;
    @use "../styles/abstracts/mixins" as mixins;
	@use "../styles/abstracts/functions" as functions;

    .variables {
		--padding: #{
			0
			functions.rem(variables.$margin-page-desktop)
		};
	}

    .gallery-search-and-filter-outer {
        position: relative;
        width: 100%;
        height: auto;

        .search-and-filter {
            position: sticky;
            top: 0;
            padding: var(--padding);
            padding-top: functions.rem(30);
            padding-bottom: functions.rem(30);
            z-index: 1;

            opacity: 0;
            transform: translateY(calc(20%));

            @include mixins.transition(.6s);

            &.is-loaded {
                transform: translateY(0);
                opacity: 1;
            }
        }

        .gallery-wrapper {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: functions.rem(20);
            padding: var(--padding);

            .card-item {
                opacity: 0;

                transform: translateY(20%) rotate3d(1, 1, 0, 45deg);

                @include mixins.transition(.6s, all, calc(.08s * var(--index)));

                &.is-loaded {
                    transform: translateY(0) rotate3d(0, 0, 0, 0);
                    opacity: 1;
                }
            }
        }
    }
</style>