import type { PageServerLoad } from './$types';
import {
	getAllDecksDecksGet,
	getAllCardsCardsGet
} from '$lib/api';
import { getAuthHeaders } from '$lib/server/auth';

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);

	const [decksRes, cardsRes] = await Promise.all([
		getAllDecksDecksGet({ headers }),
		getAllCardsCardsGet({ headers })
	]);

	return {
		decks: decksRes.data ?? [],
		cards: cardsRes.data ?? []
	};
};

