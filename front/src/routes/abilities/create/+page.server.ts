import type { PageServerLoad } from './$types';
import { getAllAbilitiesAbilitiesGet } from '$lib/api';

export const load: PageServerLoad = async () => {
	const abilitiesRes = await getAllAbilitiesAbilitiesGet();

	return {
		abilities: abilitiesRes.data ?? []
	};
};
