<script lang="ts">
    import { page } from "$app/state";
    import { fade, fly } from "svelte/transition";
    import type { DeckReadWithCards } from "$lib/api";
    import type { Creature, Element, Type, Character } from '$lib/types';
    import { DECK_MAX_LENGTH } from "$lib/constants";
    import {
		addCardToDeckDecksDeckIdCardsCardIdPost,
		removeCardFromDeckDecksDeckIdCardsCardIdDelete,
        getDeckDecksDeckIdGet
	} from '$lib/api';

    // Components
    import ButtonIcon from "$lib/components/buttons/IconButton.svelte";
    import Card360 from "$lib/components/creature/Card360.svelte";
    import HorizontalScroll from "$lib/components/HorizontalScroll.svelte";
    import StylishedText from "$lib/components/StylishedText.svelte";
    import GallerySearchAndFilter from "$lib/components/GallerySearchAndFilter.svelte";
    import IconSelector from "$lib/components/input/IconSelector.svelte";

    // Icons
    import Arrow from "$lib/assets/icons/arrow.svg?raw";
    import Cross from "$lib/assets/icons/cross.svg?raw";
    import Grid from "$lib/assets/icons/grid.svg?raw";
    import Scroll from "$lib/assets/icons/scroll.svg?raw";
	

    interface PageProps {
		data: {
			deck?: DeckReadWithCards;
            cards?: Creature[];
            elements?: Element[];
            types?: Type[];
            characters?: Character[]
		};
	}

	let { data }: PageProps = $props();
    $inspect(data);

    // Deck data
    let deck_id = $derived(data?.deck?.id);
    let deck_title = $derived(data?.deck?.name);

    //
    // It is initialised in the effect so as not to get a warning for having derived data in a state.
    //
    let cards = $state<Creature[]>([]); 
    $effect(() => {
        cards = [...(data?.deck?.cards ?? [])];
    });
    
    let refreskey = $derived(cards.length)

    // Display info
    let cardsAreLoaded = $state(false);
    let displayView = $state<'scroll' | 'grid'>('scroll');
    let scrollVelocity = $state(0);

    let showGallery = $state(true);



    // Force animation on appear
    $effect(() => {
        void page.url.pathname;

        cardsAreLoaded = false;

        requestAnimationFrame(() => {
            cardsAreLoaded = true;
        });
    });

    $effect(() => {
        void displayView;

        showGallery = false;

        setTimeout(() => {
            requestAnimationFrame(() => {
                showGallery = true;
            });
        }, 200)
        
    });

    // API handles
    async function handleRemoveCardFromDeck(cardId: number) {
        if(!deck_id) return;

		try {
			await removeCardFromDeckDecksDeckIdCardsCardIdDelete({
				path: {
					deck_id: deck_id,
					card_id: cardId
				}
			});

        // Refresh decks
        const deckResponse = await getDeckDecksDeckIdGet({ path: { deck_id } });
        if (deckResponse.data) {
            cards = [...(deckResponse.data.cards ?? [])];
        }

		} catch (err) {
			console.error('Error eliminando carta del mazo:', err);
			alert(`Hubo un error al eliminar la carta: ${(err as Error).message}`);
		}
	}

    async function handleAddCardToDeck(cardId: number) {
        if(!deck_id) return;

		try {
			await addCardToDeckDecksDeckIdCardsCardIdPost({
				path: {
					deck_id: deck_id,
					card_id: cardId
				}
			});

			// Refresh deck
            const deckResponse = await getDeckDecksDeckIdGet({ path: { deck_id } });
            if (deckResponse.data) {
                cards = [...(deckResponse.data.cards ?? [])];
            }
		} catch (err) {
			console.error('Error añadiendo carta al mazo:', err);
			alert(`Hubo un error al añadir la carta: ${(err as Error).message}`);
		}
	}

</script>

<div class="deck-container">
    <div class="deck-current-info">
        {#if deck_title}
            <div class="info" class:is-loaded={cardsAreLoaded}>
                <div class="row">
                    <div class="icon-pos">
                        <ButtonIcon
                            rotateIcon={90}
                            link="/my-collection/decks"
                            ariaLabel="Back to Decks"
                        >
                            {@html Arrow}
                        </ButtonIcon>
                    </div>
                    <StylishedText text={deck_title} fontSize={46} />
                    <p>{cards.length}/{DECK_MAX_LENGTH} Cards</p>
                </div>
                <IconSelector
                    name="display-view"
                    data={[
                        {value: 'grid', icon: Grid},
                        {value: 'scroll', icon: Scroll}
                    ]}
                    bind:group={displayView}
                />
            </div>
        {/if}
        {#if displayView === 'scroll'}
            <div
                in:fly={{ x: 50, opacity:0, delay:400, duration:400 }}
                out:fly={{ x: -50, opacity:0, duration:400 }}
                style="width: 100%;"
            >
                <HorizontalScroll
                    gap={20}
                    margin={50}
                    top={0}
                    height={320}
                    smoothFactor={1}
                    itemsLength={refreskey}
                    bind:scrollVelocity
                >
                    {#each cards as card, i (card.id + '-' + i)}
                        <div
                            class="card-item"
                            class:is-loaded={cardsAreLoaded}
                            style={`
                                --index:${i + 1};
                                --index-reverse:${cards.length - i};
                                --rotate-on-scroll:${Math.max(-45, Math.min(45, scrollVelocity))}deg;
                            `}
                        >
                            <div class="rotate-on-scroll">
                                <Card360
                                    data={card}
                                    key={i}
                                    role="button"
                                    ariaLabel="test"
                                    actionsPosition="center"
                                >
                                    <ButtonIcon
                                        theme="dark"
                                        onClick={() => handleRemoveCardFromDeck(card.id )}
                                        size={42}
                                    >
                                        {@html Cross}
                                    </ButtonIcon>
                                </Card360>
                            </div>
                        </div>
                    {/each}
                </HorizontalScroll>
            </div>
        {:else}
            <div
                in:fly={{ x: 50, opacity:0, delay:400, duration:400 }}
                out:fly={{ x: -50, opacity:0, duration:400 }}
                class="display-grid"
            >
                {#each cards as card,i}
                    <div
                        class="card-item"
                        class:is-loaded={cardsAreLoaded}
                        style={`--index:${i + 1}; --index-reverse:${cards.length - i}`}
                    >
                        <Card360
                            data={card}
                            key={i}
                            role="div"
                            showInfo={false}
                            allow360Effect={false}
                            actionsPosition="center"
                        >
                            <ButtonIcon
                                theme="dark"
                                onClick={() => handleRemoveCardFromDeck(card.id )}
                                size={42}
                            >
                                {@html Cross}
                            </ButtonIcon>
                        </Card360>
                    </div>
                {/each}
            </div>
        {/if}
    </div>
    {#if showGallery}
        <div in:fade style="width:100%">
            <GallerySearchAndFilter
                cards={data.cards}
                elements={data.elements}
                onClickAddButton={(cardId) => handleAddCardToDeck(cardId)}
                showFilters={true}
                enableAddButton={true}
            />
        </div>
    {/if}
</div>

<style lang="scss">
    @use "../../../../lib/styles/abstracts/variables" as variables;
	@use "../../../../lib/styles/abstracts/mixins" as mixins;
	@use "../../../../lib/styles/abstracts/functions" as functions;

    .deck-container {
        position: relative;
        width: 100%;
        min-height: 100dvh;
        height: auto;
        padding-top: functions.rem(200);

        @include mixins.displayFlex(column, 40, flex-start, flex-start, nowrap);

        .deck-current-info {
            width: 100%;
            overflow: hidden;

            @include mixins.displayFlex(column, 0, flex-start, flex-start, nowrap);
        

            .info {
                width: 100%;
                opacity: 0;

                transform: translateY(calc(20%));

                @include mixins.margins();
                @include mixins.displayFlex(row, 20, space-between, center, nowrap);
                @include mixins.transition(.6s);

                &.is-loaded {
                    transform: translateY(0);
                    opacity: 1;
                }

                .row {
                    @include mixins.displayFlex(row, 20, flex-start, center, nowrap);
                }

                .icon-pos {
                    height: 100%;
                    padding-bottom: functions.rem(12);
                    @include mixins.displayFlex(row, 0, center, center, nowrap);
                }

                p {
                    padding-top: functions.rem(6);
                    font-size: functions.rem(18);
                    opacity: .8;
                }
            }

            .card-item {
                flex: 1;
                max-width: functions.rem(180);
                // max-width: functions.rem(300);
                opacity: 0;
                perspective: 1000px;

                transform: translateY(20%) rotate3d(1, 1, 0, 45deg);

                @include mixins.isCardLoaded(var(--index));

                .rotate-on-scroll {
                    perspective: 1000px;
                    transform: rotateY(var(--rotate-on-scroll));
                }
            }

            .display-grid {
                display: grid;
                width: 100%;
                grid-template-columns: repeat(10, 1fr);
                gap: functions.rem(12);
                padding-top: functions.rem(34);

                @include mixins.margins();

                .card-item {
                    width: 100%;
                    max-width: none;
                    height: auto;
                }
            }
        }
    }
</style>