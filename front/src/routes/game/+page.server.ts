import type { PageServerLoad } from "./$types";
import { getAuthHeaders } from "$lib/server/auth";
import {
	getDeckSummariesDecksSummariesGet,
	listRoomsGameRoomsGet,
	getAllCardsCardsGet,
	getAllElementsGet,
} from "$lib/api";

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);

	const [decksRes, roomsRes, cardsRes, elementsRes] = await Promise.all([
		getDeckSummariesDecksSummariesGet({ headers, throwOnError: true }),
		listRoomsGameRoomsGet({ headers, throwOnError: true }),
		getAllCardsCardsGet({ headers, throwOnError: true }),
		getAllElementsGet({ headers, throwOnError: true }),
	]);

	return {
		decks: decksRes.data,
		rooms: roomsRes.data,
		cards: cardsRes.data,
		elements: elementsRes.data,
	};
};
