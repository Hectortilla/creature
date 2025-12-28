import type { PageServerLoad } from './$types';
import { PUBLIC_API_URL } from '$env/static/public';
import { getAuthHeaders } from '$lib/server/auth';
import type { DeckReadSummary, RoomSummary } from '$lib/types';

export const load: PageServerLoad = async ({ locals, fetch }) => {
	const headers = getAuthHeaders(locals);

	// Fetch decks and rooms in parallel
	const [decksResponse, roomsResponse] = await Promise.all([
		fetch(`${PUBLIC_API_URL}/decks/summaries`, {
			headers: {
				...headers,
				'Content-Type': 'application/json'
			}
		}),
		fetch(`${PUBLIC_API_URL}/game/rooms`, {
			headers: {
				...headers,
				'Content-Type': 'application/json'
			}
		})
	]);

	let decks: DeckReadSummary[] = [];
	let rooms: RoomSummary[] = [];

	try {
		if (decksResponse.ok) {
			decks = await decksResponse.json();
		}
	} catch (error) {
		console.error('Error loading decks:', error);
	}

	try {
		if (roomsResponse.ok) {
			const roomsData = await roomsResponse.json();
			rooms = roomsData.rooms || [];
		}
	} catch (error) {
		console.error('Error loading rooms:', error);
	}

	return {
		decks,
		rooms
	};
};

