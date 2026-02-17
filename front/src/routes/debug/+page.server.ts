import type { PageServerLoad } from './$types';
import { getAuthHeaders } from '$lib/server/auth';
import type { DeckReadSummary, RoomSummary } from '$lib/types';
import {
	getDeckSummariesDecksSummariesGet,
	listRoomsGameRoomsGet
} from '$lib/api';

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);

	// Fetch decks and rooms in parallel using the generated API client
	const [decksRes, roomsRes] = await Promise.all([
		getDeckSummariesDecksSummariesGet({ headers }),
		listRoomsGameRoomsGet({ headers })
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
		rooms
	};
};
