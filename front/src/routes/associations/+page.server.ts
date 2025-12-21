import type { PageServerLoad } from './$types';
import { getAllAssociationsAssociationsGet } from '$lib/api';

export const load: PageServerLoad = async () => {
	const associationsRes = await getAllAssociationsAssociationsGet();

	return {
		associations: associationsRes.data ?? []
	};
};
