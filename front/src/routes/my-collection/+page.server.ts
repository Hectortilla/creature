import type { PageServerLoad } from "./$types";
import { getAllDecksDecksGet, getAllCardsCardsGet } from "$lib/api";
import { getAuthHeaders } from "$lib/server/auth";

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);

	const decksRes = await getAllDecksDecksGet({ headers, throwOnError: true });
	const cardsRes = await getAllCardsCardsGet({ headers, throwOnError: true });

	return {
		decks_amount: decksRes.data.length,
		cards_amount: cardsRes.data.length,
	};
};
