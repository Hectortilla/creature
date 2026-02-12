<script lang="ts">
    import type { PageProps } from "./$types";
    import type { DeckReadWithCards } from '$lib/api';
    import {
		deleteDeckDecksDeckIdDelete
	} from '$lib/api';

    // Components
    import DeckCard from "$lib/components/cards/Deck.svelte";
    import HorizontalScroll from "$lib/components/HorizontalScroll.svelte";

    let { data }: PageProps = $props();
    $inspect(data);

    let decks = $derived<DeckReadWithCards[]>(data.decks ?? []);
    let selectedDeckId = $state<number | null>(null);

    async function handleDeleteDeck(deckId: number) {
		if (!confirm('¿Estás seguro de que quieres eliminar este mazo?')) {
			return;
		}

		try {
			await deleteDeckDecksDeckIdDelete({
				path: {
					deck_id: deckId
				}
			});

			// Remove from local state
			decks = decks.filter((d) => d.id !== deckId);
			if (selectedDeckId === deckId) {
				selectedDeckId = null;
			}
			alert('Mazo eliminado con éxito');
		} catch (err) {
			console.error('Error eliminando el mazo:', err);
			alert(`Hubo un error al eliminar el mazo: ${(err as Error).message}`);
		}
	}

</script>

<div class="decks-container">
    <HorizontalScroll
        gap={100}
        margin={120}
        top={12}
        smoothFactor={1}
    >
        {#each decks as deck, i}
            <DeckCard
                index={i}
                text={deck.name}
                cards={deck.cards}
                link={`/my-collection/decks/${deck.id}`}
                deleteDeck={() => handleDeleteDeck(deck.id)}
            />
        {/each}
    </HorizontalScroll>
</div>

<style lang="scss">
    @use "../../../../lib/styles/abstracts/variables" as variables;
	@use "../../../../lib/styles/abstracts/mixins" as mixins;
	@use "../../../../lib/styles/abstracts/functions" as functions;

    .decks-container {
        position: relative;
        width: 100%;
        height: 100vh; // prevent browser
        height: 100dvh;
        overflow: hidden;

        @include mixins.displayFlex(row, 0, center, center, nowrap);
    }
</style>