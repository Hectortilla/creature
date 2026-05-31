<script lang="ts">
    import { page } from '$app/state';

    // Components
    import Card360 from "$lib/components/creature/Card360.svelte";
    import ButtonIcon from "$lib/components/buttons/IconButton.svelte";
    import InputSearch from "$lib/components/input/Search.svelte";
    import IconSelector from "$lib/components/input/IconSelector.svelte";

    // Icons
    import Plus from "$lib/assets/icons/plus.svg?raw";
    import Small from "$lib/assets/icons/grid-small.svg?raw";
    import Medium from "$lib/assets/icons/grid-medium.svg?raw";

    interface Props {
        cards: any;
        elements?: any;

        // Display
        showSearch?: boolean;
        showFilters?: boolean;
        showViews?: boolean;
        enableAddButton?: boolean;

        // Events
        onClickAddButton?: (cadId:number) => void;
    }

    let {
        cards,
        // eslint-disable-next-line @typescript-eslint/no-unused-vars -- consumed in markup
        elements,
        showSearch = true,
        showFilters = true,
        showViews = true,
        enableAddButton = false,
        onClickAddButton,
    }: Props = $props();

    let cardsAreLoaded = $state(false);
    let sizeView = $state<'small' | 'medium' | 'large'>('medium');

    /* Filters */
    let search = $state("");

    let searchCardsByName = $derived(
        cards.filter((card: any) =>
            card.name
                ?.toLowerCase()
                .includes(search.toLowerCase())
    ))

    /* Handles */

    // Force animation on appear
    $effect(() => {
        void page.url.pathname;

        cardsAreLoaded = false;

        requestAnimationFrame(() => {
            cardsAreLoaded = true;
        });
    });

    $effect(() => {
        void sizeView;
        void document.body.offsetHeight;
    });
</script>

<div class="gallery-search-and-filter-outer variables">
    {#if showSearch || showFilters}
        <div class="search-and-filter" class:is-loaded={cardsAreLoaded}>
            {#if showSearch}
                <InputSearch
                    placeholder="Search by name"
                    bind:value={search}
                />
            {/if}
            {#if showFilters || showViews}
                <div class="filter-and-views">
                    {#if showViews}
                        <IconSelector
                            name="size-view"
                            data={[
                                {value: 'small', icon: Small},
                                {value: 'medium', icon: Medium}
                            ]}
                            bind:group={sizeView}
                        />
                    {/if}
                </div>
            {/if}
        </div>
    {/if}
    <div class={`gallery-wrapper size-${sizeView}`}>
        {#each searchCardsByName as card, i}
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
                    actionsPosition="center"
                >
                    {#if enableAddButton}
                        <ButtonIcon
                            theme="dark"
                            onClick={() => onClickAddButton && onClickAddButton(card.id)}
                            size={42}
                        >
                            {@html Plus}
                        </ButtonIcon>
                    {/if}
                </Card360>
            </div>
        {/each}
    </div>
</div>

<style lang="scss">
    @use "../styles/abstracts/variables" as variables;
    @use "../styles/abstracts/mixins" as mixins;
	@use "../styles/abstracts/functions" as functions;

    .variables {
		--gallery-columns-small: 8;
        --gallery-columns-medium: 6;
        --gallery-columns-large: 5;

        @media (min-width:1600px) {
            --gallery-columns-small: 10;
            --gallery-columns-medium: 8;
            --gallery-columns-large: 6;
        }

        @media (max-width:1200px) {
            --gallery-columns-small: 6;
            --gallery-columns-medium: 4;
            --gallery-columns-large: 3;
        }
        @media (max-width:800px) {
            --gallery-columns-small: 4;
            --gallery-columns-medium: 3;
            --gallery-columns-large: 2;
        }
        @media (max-width:450px) {
            --gallery-columns-small: 3;
            --gallery-columns-medium: 2;
            --gallery-columns-large: 2;
        }
        @media (max-width:375px) {
            --gallery-columns-small: 2;
            --gallery-columns-medium: 2;
            --gallery-columns-large: 1;
        }
	}

    .gallery-search-and-filter-outer {
        position: relative;
        width: 100%;
        height: auto;
        padding-bottom: functions.rem(50);

        .search-and-filter {
            position: sticky;
            top: 0;
            padding-top: functions.rem(30);
            padding-bottom: functions.rem(30);
            z-index: 1;

            opacity: 0;
            transform: translateY(calc(20%));

            @include mixins.transition(.6s);
            @include mixins.margins();
            @include mixins.displayFlex(row, 20, space-between, flex-start, nowrap);

            &.is-loaded {
                transform: translateY(0);
                opacity: 1;
            }

            .filter-and-views {
                width: max-content;

            }
        }

        .gallery-wrapper {
            display: grid;
            gap: functions.rem(20);
            height: auto;

            @include mixins.margins();

            &.size-small {grid-template-columns: repeat(var(--gallery-columns-small), 1fr); gap: functions.rem(10); }
            &.size-medium {grid-template-columns: repeat(var(--gallery-columns-medium), 1fr); gap: functions.rem(20);}
            &.size-large {grid-template-columns: repeat(var(--gallery-columns-large), 1fr); gap: functions.rem(20);}

            .card-item {
                @include mixins.isCardLoaded(var(--index));
            }
        }
    }
</style>