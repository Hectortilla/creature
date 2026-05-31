import type { PageServerLoad } from "./$types";
import { getAllAssociationsGet } from "$lib/api";
import { getAuthHeaders } from "$lib/server/auth";

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);
	const associationsRes = await getAllAssociationsGet({ headers });

	return {
		associations: associationsRes.data ?? [],
	};
};
