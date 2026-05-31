import type { PageServerLoad } from "./$types";
import { getAllDecksDecksGet, getAllCardsCardsGet } from "$lib/api";
import { getAuthHeaders } from "$lib/server/auth";

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);

	const decksRes = await getAllDecksDecksGet({ headers });
	const cardsRes = await getAllCardsCardsGet({ headers });

	return {
		decks_amount: decksRes.data?.length ?? 0,
		cards_amount: cardsRes.data?.length ?? 0,
	};
};
