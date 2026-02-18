<script lang="ts">
    import type { PageProps } from "./$types";
    import { onMount } from "svelte";
    import { fade, fly, scale } from "svelte/transition";
    import { goto } from "$app/navigation";
    import type { DeckReadWithCards } from "$lib/api";
    import type { Creature, Element, Type, Character } from '$lib/types';
    import { DECK_MAX_LENGTH } from "$lib/constants";
    import {
		getAllDecksDecksGet,
		getAllCardsCardsGet,
		createDeckDecksPost,
		addCardToDeckDecksDeckIdCardsCardIdPost,
		removeCardFromDeckDecksDeckIdCardsCardIdDelete,
		deleteDeckDecksDeckIdDelete,
        getDeckDecksDeckIdGet
	} from '$lib/api';

    // Components
    import ButtonIcon from "$lib/components/buttons/IconButton.svelte";
    import Card360 from "$lib/components/creature/Card360.svelte";
    import HorizontalScroll from "$lib/components/HorizontalScroll.svelte";
    import StylishedText from "$lib/components/StylishedText.svelte";
    import IconButton from "$lib/components/buttons/IconButton.svelte";
    import GallerySearchAndFilter from "$lib/components/GallerySearchAndFilter.svelte";

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
    let cards = $state([...(data?.deck?.cards ?? [])]);
    let refreskey = $derived(cards.length)

    // Display info
    let cardsAreLoaded = $state(false);
    let displayView = $state<'scroll' | 'grid'>('scroll');
    let scrollVelocity = $state(0);

    function onChangeDisplayView(display: 'scroll' | 'grid') {
        displayView = display;
    }

    onMount(() => {
        cardsAreLoaded = true;
    });
    

    // Events
    function ViewCardInfo(cardCode: number) {
        goto(`/old/cards/${cardCode}`);
    }


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

<div class="deck-container variables">
    {#if deck_title}
        <div class="info" class:is-loaded={cardsAreLoaded}>
            <div class="row">
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
                <p>{cards?.length}/{DECK_MAX_LENGTH} Cards</p>
            </div>
            <div class={`display-view ${displayView}`}>
                <button
                    onclick={() => onChangeDisplayView('scroll')}
                    disabled={displayView === 'scroll'}
                >
                    {@html Scroll}
                </button>
                <button
                    onclick={() => onChangeDisplayView('grid')}
                    disabled={displayView === 'grid'}
                >
                    {@html Grid}
                </button>
            </div>
        </div>
    {/if}
    {#if displayView === 'scroll'}
        <div style="width: 100%; overflow:hidden;">
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
                        out:fade={{ duration: 250 }}
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
                                onClick={() => alert("Click must open quick card data. Long click open dedicated page.")}
                                onLongClick={() => ViewCardInfo(card.code)}
                            >
                                <ButtonIcon
                                    onClick={() => handleRemoveCardFromDeck(card.id )}
                                    size={32}
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
    <GallerySearchAndFilter
        cards={data.cards}
        onClickOnCard={(cardId) => handleAddCardToDeck(cardId)}
    />
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
        padding-top: functions.rem(160);

        @include mixins.displayFlex(column, 0, flex-start, flex-start, nowrap);

        .info {
            width: 100%;
            padding: var(--padding);
            opacity: 0;

            transform: translateY(calc(20%));

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
            gap: functions.rem(12);
            padding: var(--padding);

            .card-item {
                width: 100%;
                max-width: none;
                height: auto;
            }
        }
    }

    .display-view {
        $padding-container: functions.rem(6);
        $button-size: functions.rem(34);

        position: relative;
        padding: $padding-container;
        background-color: black;
        border-radius: functions.rem(14);
        overflow: hidden;

        @include mixins.displayFlex(row, 0, flex-start, center, nowrap);

        button {
            width: $button-size;
            height: $button-size;
            padding: functions.rem(8);
            color: var(--color-icon-button-color);
            cursor: pointer;

            @include mixins.transition(all, .4s);

            &:disabled {
                filter: saturate(.4);
                opacity: .6;
                cursor: default;
                pointer-events: none;
            }
        }
    }
</style>