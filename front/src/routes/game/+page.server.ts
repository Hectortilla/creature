import type { PageServerLoad } from './$types';
import { PUBLIC_API_URL } from '$env/static/public';
import { getAuthHeaders } from '$lib/server/auth';

interface DeckSummary {
	id: number;
	name: string;
	description: string | null;
	card_count: number;
	is_valid_for_playing: boolean;
}

interface RoomSummary {
	room_id: string;
	host_id: string;
	player1_id: string | null;
	player1_name: string | null;
	player2_id: string | null;
	player2_name: string | null;
	created_at: string;
	is_full: boolean;
	is_started: boolean;
	can_join: boolean;
	players: Array<{ player_id: string; name: string } | null>;
}

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

	let decks: DeckSummary[] = [];
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

