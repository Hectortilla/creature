import type { PageServerLoad } from "./$types";
import { getAuthHeaders } from "$lib/server/auth";
import type { DeckReadSummary, RoomSummary } from "$lib/types";
import {
	getDeckSummariesDecksSummariesGet,
	listRoomsGameRoomsGet,
	getAllCardsCardsGet,
	getAllElementsGet,
} from "$lib/api";

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);

	const [decksRes, roomsRes, cardsRes, elementsRes] = await Promise.all([
		getDeckSummariesDecksSummariesGet({ headers }),
		listRoomsGameRoomsGet({ headers }),
		getAllCardsCardsGet({ headers }),
		getAllElementsGet({ headers }),
	]);

	let decks: DeckReadSummary[] = [];
	let rooms: RoomSummary[] = [];

	if (decksRes.data) {
		decks = decksRes.data as DeckReadSummary[];
	}

	if (roomsRes.data) {
		const roomsData = roomsRes.data as { rooms?: RoomSummary[] };
		rooms = roomsData.rooms || [];
	}

	return {
		decks,
		rooms,
		cards: cardsRes.data ?? [],
		elements: elementsRes.data ?? [],
	};
};
