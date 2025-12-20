import type { PageServerLoad } from './$types';
import { getAllAbilitiesAbilitiesGet } from '$lib/api/config';

export const load: PageServerLoad = async () => {
	const abilitiesRes = await getAllAbilitiesAbilitiesGet();

	return {
		abilities: abilitiesRes.data ?? []
	};
};
