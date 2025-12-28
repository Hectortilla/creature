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

export const load: PageServerLoad = async ({ locals, fetch }) => {
	const headers = getAuthHeaders(locals);

	// Use the summaries endpoint for lightweight deck data (no card details)
	try {
		const response = await fetch(`${PUBLIC_API_URL}/decks/summaries`, {
			headers: {
				...headers,
				'Content-Type': 'application/json'
			}
		});

		if (!response.ok) {
			throw new Error(`Failed to fetch decks: ${response.statusText}`);
		}

		const summaries: DeckSummary[] = await response.json();

		return {
			decks: summaries
		};
	} catch (error) {
		console.error('Error loading decks:', error);
		return {
			decks: []
		};
	}
};

