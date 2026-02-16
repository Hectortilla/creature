import type { PageServerLoad } from './$types';
import {
	getAllDecksDecksGet
} from '$lib/api';
import { getAuthHeaders } from '$lib/server/auth';

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);

	const decksRes = await getAllDecksDecksGet({ headers });

	return {
		decks: decksRes.data ?? []
	};
};

