import type { PageServerLoad } from './$types';
import {
	getDeckDecksDeckIdGet,
	getAllCardsCardsGet,
	getAllElementsGet,
	getAllTypesGet,
	getAllCharactersGet
	
} from '$lib/api';
import { getAuthHeaders } from '$lib/server/auth';

export const load: PageServerLoad = async ({ params, locals }) => {
	const headers = getAuthHeaders(locals);
	const { deck_id } = params;

	if (!deck_id) {
		throw new Error("Deck parameter is missing");
	}

	const [deckRes, cardsRes, elementsRes, typesRes, charactersRes] = await Promise.all([
		getDeckDecksDeckIdGet({ path: { deck_id: Number(deck_id) }, headers }),
		getAllCardsCardsGet({ headers }),
		getAllElementsGet({ headers }),
		getAllTypesGet({ headers }),
		getAllCharactersGet({ headers })
	]);

	return {
		deck: deckRes.data ?? [],
		cards: cardsRes.data ?? [],
		elements: elementsRes.data ?? [],
		types: typesRes.data ?? [],
		characters: charactersRes.data ?? []
	};
};

