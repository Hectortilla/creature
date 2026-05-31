import type { PageServerLoad } from "./$types";
import { getAllAttacksAttacksGet, getAllElementsGet } from "$lib/api";
import { getAuthHeaders } from "$lib/server/auth";

export const load: PageServerLoad = async ({ locals }) => {
	const headers = getAuthHeaders(locals);

	const [attacksRes, elementsRes] = await Promise.all([
		getAllAttacksAttacksGet({ headers }),
		getAllElementsGet({ headers }),
	]);

	return {
		attacks: attacksRes.data ?? [],
		elements: elementsRes.data ?? [],
	};
};
