import type { PageServerLoad } from './$types';
import {
	getDeckDecksDeckIdGet
	
} from '$lib/api';
import { getAuthHeaders } from '$lib/server/auth';

export const load: PageServerLoad = async ({ params, locals }) => {
	const headers = getAuthHeaders(locals);
	const { deck_id } = params;

	if (!deck_id) {
		throw new Error("Deck parameter is missing");
	}

	const deckRes = await getDeckDecksDeckIdGet({ path: { deck_id: Number(deck_id) }, headers });

	return {
		deck: deckRes.data ?? []
	};
};

