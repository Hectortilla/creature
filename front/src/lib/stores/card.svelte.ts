import { browser } from '$app/environment';
import { getAllCardsCardsGet, getCardCardsValueGet } from '$lib/api';
import type { CardReadWithRelations } from '$lib/api/types.gen';
import { shouldPersist } from '$lib/utils';


function createCardStore() {
	let cards = $state<CardReadWithRelations[]>([shouldPersist() ? JSON.parse(localStorage.getItem('cards') ?? '[]') : []]);
	let loading = $state(false);
	let fetchPromise: Promise<void> | null = null;

	async function fetchCards() {
		if (loading || cards.length > 0) return fetchPromise ?? Promise.resolve();

		loading = true;

		fetchPromise = (async () => {
			try {
				const fetchedCards = (await getAllCardsCardsGet({})).data ?? [];
				cards = fetchedCards;
				if (shouldPersist())
					localStorage.setItem('cards', JSON.stringify(fetchedCards));
			} finally {
				loading = false;
				fetchPromise = null;
			}
		})();

		return fetchPromise;
	}

	async function getCard(id: number): Promise<CardReadWithRelations | null> {
		if (loading)
			await fetchPromise;
		else if (cards.length === 0)
			await fetchCards();

		return cards.find((card) => card.id === id) ?? null;
	}

	return {
		get cards() {
			return cards;
		},
		get loading() {
			return loading;
		},
		fetchCards,
		getCard,
	};
}

export const cardStore = createCardStore();

