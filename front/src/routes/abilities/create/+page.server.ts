import type { PageServerLoad } from './$types';
import { getAllAbilitiesAbilitiesGet } from '$lib/api';
import { getAuthHeaders } from '$lib/server/auth';

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);
	const abilitiesRes = await getAllAbilitiesAbilitiesGet({ headers });

	return {
		abilities: abilitiesRes.data ?? []
	};
};
