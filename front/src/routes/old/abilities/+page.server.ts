import type { PageServerLoad } from "./$types";
import { getAllAbilitiesGet } from "$lib/api";
import { getAuthHeaders } from "$lib/server/auth";

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);
	const abilitiesRes = await getAllAbilitiesGet({ headers });

	return {
		abilities: abilitiesRes.data ?? [],
	};
};
